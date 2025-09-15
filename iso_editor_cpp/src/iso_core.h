#ifndef ISOCORE_H
#define ISOCORE_H

#include <QString>
#include <QList>
#include <QDateTime>
#include <QByteArray>

#include <cdio/cdio.h> // For lsn_t

// Represents a file or directory within the ISO structure.
struct IsoNode
{
    QString name;
    bool isDirectory = false;
    bool isHidden = false;
    quint64 size = 0;
    QDateTime date;

    QByteArray fileData;
    bool isNew = false;
    lsn_t lsn = 0;

    QList<IsoNode*> children;
    IsoNode* parent = nullptr;

    ~IsoNode() {
        qDeleteAll(children);
    }
};

// Represents the volume information of the ISO.
struct VolumeDescriptor
{
    QString systemId;
    QString volumeId;
};

// This class will encapsulate all the logic for ISO manipulation.
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
    void importDirectory(const QString &dirPath, IsoNode *targetNode);
    void addFolderToDirectory(const QString &folderName, IsoNode *targetNode);
    void removeNode(IsoNode *node);
    QByteArray getFileData(const IsoNode* node) const;

    // Getters
    const IsoNode* getDirectoryTree() const;
    IsoNode* getDirectoryTree();
    const VolumeDescriptor& getVolumeDescriptor() const;
    QString getBootImagePath() const;
    QString getEfiBootImagePath() const;
    bool isModified() const;

    // Setters
    void setVolumeDescriptor(const VolumeDescriptor& vd);
    void setBootImagePath(const QString& path);
    void setEfiBootImagePath(const QString& path);

private:
    void clear();

    IsoNode* rootNode;
    VolumeDescriptor volumeDescriptor;
    QString bootImagePath;
    QString efiBootImagePath;
    bool modified;
    QString currentIsoPath;
};

#endif // ISOCORE_H
