#include "iso_core.h"

#include <QDebug>
#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QTemporaryDir>
#include <QProcess>

#include <cdio++/iso9660.hpp>
#include <memory>
#include <time.h>

// Forward declaration for the recursive helper
static bool writeTreeToDisk(const ISOCore* core, const IsoNode* node, const QString& currentPath);


// Helper function to recursively build our internal tree from libcdio's tree
static void buildNodeTree(ISO9660::IFS &fs, const std::string& path, IsoNode* parent_node)
{
    stat_vector_t stat_vector;
    if (!fs.readdir(path.c_str(), stat_vector)) {
        return;
    }

    for (ISO9660::Stat* stat_obj : stat_vector) {
        if (strcmp(stat_obj->p_stat->filename, ".") == 0 || strcmp(stat_obj->p_stat->filename, "..") == 0) {
            continue;
        }

        IsoNode* new_node = new IsoNode();
        new_node->name = QString::fromStdString(stat_obj->p_stat->filename);
        new_node->parent = parent_node;
        new_node->isNew = false;
        new_node->lsn = stat_obj->p_stat->lsn;

        time_t timestamp = mktime(&stat_obj->p_stat->tm);
        new_node->date = QDateTime::fromSecsSinceEpoch(timestamp);

        if (stat_obj->p_stat->type == iso9660_stat_s::_STAT_DIR) {
            new_node->isDirectory = true;
            new_node->size = 0;
            std::string new_path = path;
            if (new_path.back() != '/') new_path += '/';
            new_path += stat_obj->p_stat->filename;
            buildNodeTree(fs, new_path, new_node);
        } else {
            new_node->isDirectory = false;
            new_node->size = stat_obj->p_stat->size;
        }

        parent_node->children.append(new_node);
    }

    for (ISO9660::Stat* stat_obj : stat_vector) {
        stat_obj->p_stat = nullptr;
        delete stat_obj;
    }
}


ISOCore::ISOCore()
{
    rootNode = nullptr;
    modified = false;
    initNewIso();
}

ISOCore::~ISOCore()
{
    clear();
}

void ISOCore::clear()
{
    delete rootNode;
    rootNode = nullptr;
    modified = false;
    currentIsoPath.clear();
    bootImagePath.clear();
    efiBootImagePath.clear();
    volumeDescriptor = VolumeDescriptor();
}

void ISOCore::initNewIso()
{
    clear();

    rootNode = new IsoNode();
    rootNode->name = "/";
    rootNode->isDirectory = true;
    rootNode->parent = rootNode;
    rootNode->date = QDateTime::currentDateTime();
    rootNode->isNew = true;

    volumeDescriptor.volumeId = "NEW_ISO";
    modified = false;
}

bool ISOCore::loadIso(const QString &filePath)
{
    initNewIso();

    ISO9660::IFS fs;
    if (!fs.open(filePath.toStdString().c_str(), ISO_EXTENSION_ALL)) {
        qWarning() << "Failed to open ISO:" << filePath;
        initNewIso();
        return false;
    }

    char* vol_id = nullptr;
    if (fs.get_volume_id(vol_id) && vol_id) {
        volumeDescriptor.volumeId = QString(vol_id).trimmed();
        free(vol_id);
    }

    char* sys_id = nullptr;
    if (fs.get_system_id(sys_id) && sys_id) {
        volumeDescriptor.systemId = QString(sys_id).trimmed();
        free(sys_id);
    }

    buildNodeTree(fs, "/", rootNode);

    fs.close();
    currentIsoPath = filePath;
    modified = false;
    rootNode->isNew = false;
    return true;
}

QByteArray ISOCore::getFileData(const IsoNode* node) const
{
    if (!node || node->isDirectory) return QByteArray();
    if (node->isNew) return node->fileData;
    if (currentIsoPath.isEmpty()) return QByteArray();

    iso9660_t* p_iso = iso9660_open(currentIsoPath.toStdString().c_str());
    if (!p_iso) return QByteArray();

    QByteArray buffer;
    buffer.resize(node->size);

    long int bytes_to_read_in_blocks = node->size / ISO_BLOCKSIZE;
    if (node->size % ISO_BLOCKSIZE > 0) {
        bytes_to_read_in_blocks++;
    }

    long int bytes_read = iso9660_iso_seek_read(p_iso, buffer.data(), node->lsn, bytes_to_read_in_blocks);
    iso9660_close(p_iso);

    buffer.resize(node->size);
    return buffer;
}


bool ISOCore::saveIso(const QString &filePath)
{
    QTemporaryDir tempDir;
    if (!tempDir.isValid()) {
        qWarning() << "Failed to create temporary directory.";
        return false;
    }

    if (!writeTreeToDisk(this, rootNode, tempDir.path())) {
        qWarning() << "Failed to write ISO contents to temporary directory.";
        return false;
    }

    QStringList args;
    args << "-o" << filePath;
    args << "-R" << "-J";
    args << "-V" << volumeDescriptor.volumeId; // Set Volume ID
    args << "-sysid" << volumeDescriptor.systemId;

    if (!bootImagePath.isEmpty()) {
        // Need to copy the boot image into the temp dir for genisoimage to find it
        QFileInfo bootInfo(bootImagePath);
        QString bootTempPath = tempDir.path() + "/" + bootInfo.fileName();
        if (QFile::copy(bootImagePath, bootTempPath)) {
            args << "-b" << bootInfo.fileName();
        } else {
            qWarning() << "Could not copy boot image to temp directory.";
        }
    }
    // Note: genisoimage support for EFI is more complex and often requires -eltorito-boot
    // and other options. This is a simplified version.

    args << tempDir.path();

    QProcess genisoimage;
    genisoimage.start("genisoimage", args);
    if (!genisoimage.waitForFinished(-1)) {
        qWarning() << "genisoimage process failed to finish:" << genisoimage.errorString();
        return false;
    }

    if (genisoimage.exitCode() != 0) {
        qWarning() << "genisoimage failed with exit code" << genisoimage.exitCode();
        qWarning() << genisoimage.readAllStandardError();
        return false;
    }

    modified = false;
    currentIsoPath = filePath;
    return true;
}

void ISOCore::importDirectory(const QString &dirPath, IsoNode *targetNode)
{
    if (!targetNode || !targetNode->isDirectory) return;

    QFileInfo dirInfo(dirPath);
    if (!dirInfo.isDir()) return;

    // First, create a new directory node in the target
    addFolderToDirectory(dirInfo.fileName(), targetNode);

    // Find the newly created node
    IsoNode* newDirNode = nullptr;
    for (IsoNode* child : targetNode->children) {
        if (child->isDirectory && child->name == dirInfo.fileName()) {
            newDirNode = child;
            break;
        }
    }

    if (!newDirNode) return; // Should not happen

    QDirIterator it(dirPath, QDir::Files | QDir::Dirs | QDir::NoDotAndDotDot, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        it.next();
        QString path = it.filePath();
        QString relativePath = path;
        relativePath.remove(0, dirPath.length() + 1);

        QFileInfo info(path);

        // This is a simplified import. A real one would need to reconstruct the
        // directory structure perfectly within the targetNode.
        // For now, we will just add all files to the new directory node.
        if (info.isFile()) {
            addFileToDirectory(path, newDirNode);
        }
    }
    modified = true;
}

void ISOCore::addFileToDirectory(const QString &filePath, IsoNode *targetNode)
{
    if (!targetNode || !targetNode->isDirectory) return;

    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly)) {
        qWarning() << "Could not open file for reading:" << filePath;
        return;
    }

    QByteArray fileData = file.readAll();
    QFileInfo fileInfo(filePath);
    QString filename = fileInfo.fileName();

    for (int i = 0; i < targetNode->children.size(); ++i) {
        if (!targetNode->children[i]->isDirectory && targetNode->children[i]->name.compare(filename, Qt::CaseInsensitive) == 0) {
            delete targetNode->children.takeAt(i);
            break;
        }
    }

    IsoNode* newNode = new IsoNode();
    newNode->name = filename;
    newNode->isDirectory = false;
    newNode->parent = targetNode;
    newNode->date = fileInfo.lastModified();
    newNode->size = fileData.size();
    newNode->isNew = true;
    newNode->fileData = fileData;

    targetNode->children.append(newNode);
    modified = true;
}

void ISOCore::addFolderToDirectory(const QString &folderName, IsoNode *targetNode)
{
    if (!targetNode || !targetNode->isDirectory) return;

    for (const IsoNode* child : targetNode->children) {
        if (child->isDirectory && child->name.compare(folderName, Qt::CaseInsensitive) == 0) {
            qWarning() << "Folder" << folderName << "already exists.";
            return;
        }
    }

    IsoNode* newNode = new IsoNode();
    newNode->name = folderName;
    newNode->isDirectory = true;
    newNode->parent = targetNode;
    newNode->date = QDateTime::currentDateTime();
    newNode->isNew = true;

    targetNode->children.append(newNode);
    modified = true;
}

void ISOCore::removeNode(IsoNode *node)
{
    if (!node || !node->parent || node == rootNode) {
        qWarning() << "Cannot remove root node or node with no parent.";
        return;
    }

    IsoNode* parent = node->parent;
    if (parent->children.removeOne(node)) {
        delete node;
        modified = true;
    } else {
        qWarning() << "Could not find node" << node->name << "in its parent's children list.";
    }
}

const IsoNode* ISOCore::getDirectoryTree() const { return rootNode; }
IsoNode* ISOCore::getDirectoryTree() { return rootNode; }
const VolumeDescriptor& ISOCore::getVolumeDescriptor() const { return volumeDescriptor; }
QString ISOCore::getBootImagePath() const { return bootImagePath; }
QString ISOCore::getEfiBootImagePath() const { return efiBootImagePath; }
bool ISOCore::isModified() const { return modified; }

void ISOCore::setVolumeDescriptor(const VolumeDescriptor& vd) {
    if (volumeDescriptor.volumeId != vd.volumeId || volumeDescriptor.systemId != vd.systemId) {
        volumeDescriptor = vd;
        modified = true;
    }
}
void ISOCore::setBootImagePath(const QString& path) {
    if (bootImagePath != path) {
        bootImagePath = path;
        modified = true;
    }
}
void ISOCore::setEfiBootImagePath(const QString& path) {
    if (efiBootImagePath != path) {
        efiBootImagePath = path;
        modified = true;
    }
}

// Implementation of the recursive helper
static bool writeTreeToDisk(const ISOCore* core, const IsoNode* node, const QString& currentPath) {
    if (!node) return false;

    for (const IsoNode* child : node->children) {
        QString childPath = currentPath + QDir::separator() + child->name;
        if (child->isDirectory) {
            QDir dir(currentPath);
            if (!dir.mkdir(child->name)) {
                qWarning() << "Failed to create directory" << childPath;
                return false;
            }
            if (!writeTreeToDisk(core, child, childPath)) {
                return false;
            }
        } else {
            QFile file(childPath);
            if (!file.open(QIODevice::WriteOnly)) {
                qWarning() << "Failed to open file for writing" << childPath;
                return false;
            }
            QByteArray data = core->getFileData(child);
            if (file.write(data) != data.size()) {
                qWarning() << "Failed to write all data to file" << childPath;
                return false;
            }
        }
    }
    return true;
}
