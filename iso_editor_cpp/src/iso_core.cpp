#include "iso_core.h"

#include <QDebug>
#include <QFileInfo>

#include <cdio++/iso9660.hpp>
#include <memory>
#include <time.h>

// Helper function to recursively build our internal tree from libcdio's tree
static void buildNodeTree(ISO9660::IFS &fs, const std::string& path, IsoNode* parent_node)
{
    stat_vector_t stat_vector;
    if (!fs.readdir(path.c_str(), stat_vector)) {
        return;
    }

    for (ISO9660::Stat* stat_obj : stat_vector) {
        // Skip '.' and '..' entries
        if (strcmp(stat_obj->p_stat->filename, ".") == 0 || strcmp(stat_obj->p_stat->filename, "..") == 0) {
            continue; // The stat_vector will be cleaned up at the end of the function.
        }

        IsoNode* new_node = new IsoNode();
        new_node->name = QString::fromStdString(stat_obj->p_stat->filename);
        new_node->parent = parent_node;

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

    // WORKAROUND: The `readdir` C++ wrapper in `libiso9660++` has a memory management bug.
    // 1. It allocates `ISO9660::Stat` objects via `new`.
    // 2. The underlying C function `iso9660_ifs_readdir` allocates `iso9660_stat_t` structs.
    // 3. The `ISO9660::Stat` destructor calls `iso9660_stat_free` on the C struct.
    // 4. The `readdir` wrapper *also* calls `iso9660_filelist_free`, which appears to free the C structs again.
    // This leads to a double-free crash.
    // To work around this, we must take ownership of cleaning up the C++ `Stat` objects,
    // but prevent them from freeing the underlying C struct. We do this by detaching
    // the C pointer (`p_stat`) before deleting the C++ wrapper object. This cleans up
    // the C++ heap allocation while letting the library manage the C-level allocations.
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

    volumeDescriptor.volumeId = "NEW_ISO";
    modified = false;
}

bool ISOCore::loadIso(const QString &filePath)
{
    qDebug() << "Attempting to load ISO from" << filePath;
    initNewIso(); // Clear existing state

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

    // Build the tree
    buildNodeTree(fs, "/", rootNode);

    fs.close();
    currentIsoPath = filePath;
    modified = false;
    return true;
}

bool ISOCore::saveIso(const QString &filePath)
{
    qDebug() << "Stub: Attempting to save ISO to" << filePath;
    modified = false;
    return true;
}

void ISOCore::addFileToDirectory(const QString &filePath, IsoNode *targetNode)
{
    qDebug() << "Stub: Adding file" << filePath << "to node" << targetNode->name;
    modified = true;
}

void ISOCore::addFolderToDirectory(const QString &folderName, IsoNode *targetNode)
{
    qDebug() << "Stub: Adding folder" << folderName << "to node" << targetNode->name;
    modified = true;
}

void ISOCore::removeNode(IsoNode *node)
{
    qDebug() << "Stub: Removing node" << node->name;
    modified = true;
}

const IsoNode* ISOCore::getDirectoryTree() const
{
    return rootNode;
}

const VolumeDescriptor& ISOCore::getVolumeDescriptor() const
{
    return volumeDescriptor;
}

bool ISOCore::isModified() const
{
    return modified;
}
