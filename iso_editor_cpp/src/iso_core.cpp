#include "iso_core.h"

#include <QDebug>
#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QTemporaryDir>
#include <QProcess>
#include <QTextStream>

#include <cdio++/iso9660.hpp>
#include <memory>
#include <time.h>
#include "CUEParser.h"

// Forward declarations
static bool writeTreeToDisk(const ISOCore* core, const IsoNode* node, const QString& currentPath);
static void importDirectoryRecursive(ISOCore* core, const QString& sourcePath, IsoNode* targetParentNode);
static void buildNodeTree(ISO9660::IFS &fs, const std::string& path, IsoNode* parent_node);


// --- ISOCore Implementation ---

ISOCore::ISOCore() {
    rootNode = nullptr;
    modified = false;
    initNewIso();
}

ISOCore::~ISOCore() {
    clear();
}

void ISOCore::clear() {
    delete rootNode;
    rootNode = nullptr;
    modified = false;
    currentIsoPath.clear();
    bootImagePath.clear();
    efiBootImagePath.clear();
    volumeDescriptor = VolumeDescriptor();
}

void ISOCore::initNewIso() {
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

bool ISOCore::loadCueSheet(const QString &filePath) {
    QFile cueFile(filePath);
    if (!cueFile.open(QIODevice::ReadOnly | QIODevice::Text)) {
        qWarning() << "Failed to open CUE file:" << filePath;
        return false;
    }
    QTextStream in(&cueFile);
    QString cueData = in.readAll();
    cueFile.seek(0);
    QString cueTitle, binFile;
    while (!in.atEnd()) {
        QString line = in.readLine().trimmed();
        if (line.startsWith("TITLE", Qt::CaseInsensitive)) cueTitle = line.mid(5).trimmed().remove('"');
        if (line.startsWith("FILE", Qt::CaseInsensitive)) binFile = line.mid(4).trimmed().section('"', 1, 1);
    }
    if (binFile.isEmpty()) {
        qWarning() << "CUE sheet does not specify a BIN file.";
        return false;
    }
    CUEParser parser(cueData.toStdString().c_str());
    initNewIso();
    volumeDescriptor.volumeId = cueTitle;
    QFileInfo cueInfo(filePath);
    QString binPath = cueInfo.dir().filePath(binFile);
    const CUETrackInfo* track;
    while ((track = parser.next_track()) != nullptr) {
        IsoNode* newNode = new IsoNode();
        newNode->name = QString("Track %1.wav").arg(track->track_number, 2, 10, QChar('0'));
        newNode->parent = rootNode;
        newNode->isNew = false;
        newNode->isDirectory = false;
        newNode->isCueTrack = true;
        newNode->cueBinFile = binPath;
        newNode->cueOffset = track->data_start * 2352;
        rootNode->children.append(newNode);
    }
    for (int i = 0; i < rootNode->children.size(); ++i) {
        IsoNode* currentTrack = rootNode->children[i];
        if (i + 1 < rootNode->children.size()) {
            currentTrack->size = rootNode->children[i+1]->cueOffset - currentTrack->cueOffset;
        } else {
            QFileInfo binInfo(binPath);
            if (binInfo.exists()) currentTrack->size = binInfo.size() - currentTrack->cueOffset;
        }
    }
    currentIsoPath = filePath;
    modified = false;
    return true;
}

bool ISOCore::loadIso(const QString &filePath) {
    QFileInfo fileInfo(filePath);
    if (fileInfo.suffix().compare("cue", Qt::CaseInsensitive) == 0) {
        return loadCueSheet(filePath);
    }
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

QByteArray ISOCore::getFileData(const IsoNode* node) const {
    if (!node || node->isDirectory) return QByteArray();
    if (node->isNew) return node->fileData;
    if (node->isCueTrack) {
        QFile binFile(node->cueBinFile);
        if (!binFile.open(QIODevice::ReadOnly)) {
            qWarning() << "Could not open BIN file:" << node->cueBinFile;
            return QByteArray();
        }
        binFile.seek(node->cueOffset);
        return binFile.read(node->size);
    }
    if (currentIsoPath.isEmpty()) return QByteArray();
    iso9660_t* p_iso = iso9660_open(currentIsoPath.toStdString().c_str());
    if (!p_iso) return QByteArray();
    QByteArray buffer;
    buffer.resize(node->size);
    long int blocks = node->size / ISO_BLOCKSIZE + (node->size % ISO_BLOCKSIZE > 0);
    iso9660_iso_seek_read(p_iso, buffer.data(), node->lsn, blocks);
    iso9660_close(p_iso);
    buffer.resize(node->size);
    return buffer;
}

bool ISOCore::saveIso(const QString &filePath, bool useUdf, bool makeHybrid) {
    QTemporaryDir tempDir;
    if (!tempDir.isValid()) return false;
    if (!writeTreeToDisk(this, rootNode, tempDir.path())) return false;
    QStringList args;
    args << "-o" << filePath << "-R" << "-J" << "-V" << volumeDescriptor.volumeId << "-sysid" << volumeDescriptor.systemId;
    if (useUdf) args << "-udf";
    if (!bootImagePath.isEmpty()) {
        QFileInfo bootInfo(bootImagePath);
        if (QFile::copy(bootImagePath, tempDir.path() + "/" + bootInfo.fileName())) {
            args << "-b" << bootInfo.fileName() << "-no-emul-boot";
        }
    }
    if (!efiBootImagePath.isEmpty()) {
        QFileInfo efiInfo(efiBootImagePath);
        if (QFile::copy(efiBootImagePath, tempDir.path() + "/" + efiInfo.fileName())) {
            args << "-eltorito-boot" << efiInfo.fileName() << "-no-emul-boot";
            if (makeHybrid) args << "-isohybrid-gpt-basdat";
        }
    } else if (makeHybrid) {
        args << "-isohybrid-mbr";
    }
    args << tempDir.path();
    QProcess genisoimage;
    genisoimage.start("genisoimage", args);
    if (!genisoimage.waitForFinished(-1) || genisoimage.exitCode() != 0) {
        qWarning() << "genisoimage failed:" << genisoimage.readAllStandardError();
        return false;
    }
    modified = false;
    currentIsoPath = filePath;
    return true;
}

void ISOCore::importDirectory(const QString &dirPath, IsoNode *targetNode) {
    if (!targetNode || !targetNode->isDirectory) return;
    QFileInfo dirInfo(dirPath);
    if (!dirInfo.isDir()) return;
    importDirectoryRecursive(this, dirPath, targetNode);
    modified = true;
}

void ISOCore::addFileToDirectory(const QString &filePath, IsoNode *targetNode) {
    if (!targetNode || !targetNode->isDirectory) return;
    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly)) return;
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
    newNode->parent = targetNode;
    newNode->date = fileInfo.lastModified();
    newNode->size = fileData.size();
    newNode->isNew = true;
    newNode->fileData = fileData;
    targetNode->children.append(newNode);
    modified = true;
}

void ISOCore::addFolderToDirectory(const QString &folderName, IsoNode *targetNode) {
    if (!targetNode || !targetNode->isDirectory) return;
    for (const IsoNode* child : targetNode->children) {
        if (child->isDirectory && child->name.compare(folderName, Qt::CaseInsensitive) == 0) return;
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

void ISOCore::removeNode(IsoNode *node) {
    if (!node || !node->parent || node == rootNode) return;
    if (node->parent->children.removeOne(node)) {
        delete node;
        modified = true;
    }
}

// Getters and Setters
const IsoNode* ISOCore::getDirectoryTree() const { return rootNode; }
IsoNode* ISOCore::getDirectoryTree() { return rootNode; }
const VolumeDescriptor& ISOCore::getVolumeDescriptor() const { return volumeDescriptor; }
QString ISOCore::getBootImagePath() const { return bootImagePath; }
QString ISOCore::getEfiBootImagePath() const { return efiBootImagePath; }
bool ISOCore::isModified() const { return modified; }
QString ISOCore::getCurrentPath() const { return currentIsoPath; }
void ISOCore::setVolumeDescriptor(const VolumeDescriptor& vd) { if (volumeDescriptor.volumeId != vd.volumeId || volumeDescriptor.systemId != vd.systemId) { volumeDescriptor = vd; modified = true; } }
void ISOCore::setBootImagePath(const QString& path) { if (bootImagePath != path) { bootImagePath = path; modified = true; } }
void ISOCore::setEfiBootImagePath(const QString& path) { if (efiBootImagePath != path) { efiBootImagePath = path; modified = true; } }


// --- Static Helper Implementations ---

static void buildNodeTree(ISO9660::IFS &fs, const std::string& path, IsoNode* parent_node) {
    stat_vector_t stat_vector;
    if (!fs.readdir(path.c_str(), stat_vector)) return;
    for (ISO9660::Stat* stat_obj : stat_vector) {
        if (strcmp(stat_obj->p_stat->filename, ".") == 0 || strcmp(stat_obj->p_stat->filename, "..") == 0) continue;
        IsoNode* new_node = new IsoNode();
        new_node->name = QString::fromStdString(stat_obj->p_stat->filename);
        new_node->parent = parent_node;
        new_node->isNew = false;
        new_node->lsn = stat_obj->p_stat->lsn;
        time_t timestamp = mktime(&stat_obj->p_stat->tm);
        new_node->date = QDateTime::fromSecsSinceEpoch(timestamp);
        if (stat_obj->p_stat->type == iso9660_stat_s::_STAT_DIR) {
            new_node->isDirectory = true;
            std::string new_path = path;
            if (new_path.back() != '/') new_path += '/';
            new_path += stat_obj->p_stat->filename;
            buildNodeTree(fs, new_path, new_node);
        } else {
            new_node->size = stat_obj->p_stat->size;
        }
        parent_node->children.append(new_node);
    }
    for (ISO9660::Stat* stat_obj : stat_vector) {
        stat_obj->p_stat = nullptr;
        delete stat_obj;
    }
}

static bool writeTreeToDisk(const ISOCore* core, const IsoNode* node, const QString& currentPath) {
    if (!node) return false;
    for (const IsoNode* child : node->children) {
        QString childPath = currentPath + QDir::separator() + child->name;
        if (child->isDirectory) {
            if (!QDir(currentPath).mkdir(child->name) || !writeTreeToDisk(core, child, childPath)) return false;
        } else {
            QFile file(childPath);
            if (!file.open(QIODevice::WriteOnly)) return false;
            QByteArray data = core->getFileData(child);
            if (file.write(data) != data.size()) return false;
        }
    }
    return true;
}

static void importDirectoryRecursive(ISOCore* core, const QString& sourcePath, IsoNode* targetParentNode) {
    QDir sourceDir(sourcePath);
    QFileInfo dirInfo(sourcePath);
    core->addFolderToDirectory(dirInfo.fileName(), targetParentNode);
    IsoNode* newDirNode = nullptr;
    for (IsoNode* child : targetParentNode->children) {
        if (child->isDirectory && child->name == dirInfo.fileName()) {
            newDirNode = child;
            break;
        }
    }
    if (!newDirNode) return;
    QFileInfoList entries = sourceDir.entryInfoList(QDir::Dirs | QDir::Files | QDir::NoDotAndDotDot);
    for (const QFileInfo& entryInfo : entries) {
        if (entryInfo.isDir()) {
            importDirectoryRecursive(core, entryInfo.filePath(), newDirNode);
        } else if (entryInfo.isFile()) {
            core->addFileToDirectory(entryInfo.filePath(), newDirNode);
        }
    }
}
