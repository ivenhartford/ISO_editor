#ifndef ISOCORE_H
#define ISOCORE_H

#include <QString>
#include <QList>
#include <QDateTime>

// Represents a file or directory within the ISO structure.
struct IsoNode
{
    QString name;
    bool isDirectory = false;
    bool isHidden = false;
    quint64 size = 0;
    QDateTime date;

    QList<IsoNode*> children;
    IsoNode* parent = nullptr;

    // A simple way to clean up the tree.
    // A real implementation might use smart pointers.
    ~IsoNode() {
        qDeleteAll(children);
    }
};

// Represents the volume information of the ISO.
struct VolumeDescriptor
{
    QString systemId;
    QString volumeId;
    quint64 volumeSize = 0;
    int logicalBlockSize = 2048;
};

// This class will encapsulate all the logic for ISO manipulation.
// For now, it's just a placeholder (a "stub").
class ISOCore
{
public:
    ISOCore();
    ~ISOCore();

    void initNewIso();
    bool loadIso(const QString &filePath);
    bool saveIso(const QString &filePath);

    // Methods to interact with the file tree
    void addFileToDirectory(const QString &filePath, IsoNode *targetNode);
    void addFolderToDirectory(const QString &folderName, IsoNode *targetNode);
    void removeNode(IsoNode *node);

    // Getters for UI state
    const IsoNode* getDirectoryTree() const;
    const VolumeDescriptor& getVolumeDescriptor() const;
    bool isModified() const;

private:
    void clear(); // Helper to clean up the tree

    IsoNode* rootNode;
    VolumeDescriptor volumeDescriptor;
    bool modified;
    QString currentIsoPath;
};

#endif // ISOCORE_H
