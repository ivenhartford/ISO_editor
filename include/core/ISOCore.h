#ifndef ISOCORE_H
#define ISOCORE_H

#include <QString>
#include <QList>
#include <QMap>
#include <QVariant>
#include <memory>

// Forward declarations
struct IsoImage;
struct IsoDir;

/**
 * @brief Core class for ISO file manipulation
 *
 * This class encapsulates all ISO-related operations including:
 * - Creating new ISOs
 * - Loading existing ISOs (ISO 9660, Joliet, Rock Ridge, UDF)
 * - Modifying ISO structure (add/remove files and directories)
 * - Saving ISOs with various options
 * - Managing boot configuration (El Torito)
 *
 * Uses libisofs for ISO manipulation.
 */
class ISOCore {
public:
    /**
     * @brief Constructs a new ISOCore instance
     */
    ISOCore();

    /**
     * @brief Destructor - cleans up ISO resources
     */
    ~ISOCore();

    // ISO Operations
    /**
     * @brief Initializes a new empty ISO
     */
    void initNewIso();

    /**
     * @brief Loads an ISO file
     * @param filePath Path to the ISO file
     * @return true if successful, false otherwise
     */
    bool loadIso(const QString& filePath);

    /**
     * @brief Saves the ISO to a file
     * @param filePath Path where to save the ISO
     * @param options Save options (UDF, Joliet, Rock Ridge, etc.)
     * @return true if successful, false otherwise
     */
    bool saveIso(const QString& filePath, const QMap<QString, QVariant>& options);

    /**
     * @brief Closes the currently open ISO
     */
    void closeIso();

    // Volume Descriptor Getters/Setters
    QString getVolumeId() const;
    void setVolumeId(const QString& volumeId);

    QString getSystemId() const;
    void setSystemId(const QString& systemId);

    uint64_t getVolumeSize() const;

    // Boot Configuration
    QString getBootImagePath() const;
    void setBootImagePath(const QString& path);

    QString getEfiBootImagePath() const;
    void setEfiBootImagePath(const QString& path);

    QString getBootEmulationType() const;
    void setBootEmulationType(const QString& type);

    /**
     * @brief Gets extracted boot information from loaded ISO
     * @return List of boot entry information maps
     */
    QList<QMap<QString, QVariant>> getExtractedBootInfo() const;

    // File/Directory Operations
    /**
     * @brief Adds a file to the ISO
     * @param hostPath Path on the host filesystem
     * @param isoPath Path in the ISO
     * @return true if successful
     */
    bool addFile(const QString& hostPath, const QString& isoPath);

    /**
     * @brief Adds a directory to the ISO
     * @param hostPath Path on the host filesystem
     * @param isoPath Path in the ISO
     * @param recursive Whether to add subdirectories
     * @return true if successful
     */
    bool addDirectory(const QString& hostPath, const QString& isoPath, bool recursive = true);

    /**
     * @brief Removes a file or directory from the ISO
     * @param isoPath Path in the ISO
     * @return true if successful
     */
    bool removeNode(const QString& isoPath);

    /**
     * @brief Creates an empty directory in the ISO
     * @param isoPath Path in the ISO
     * @return true if successful
     */
    bool createDirectory(const QString& isoPath);

    // State Queries
    bool isModified() const;
    void setModified(bool modified);

    bool isLoaded() const;
    QString getCurrentIsoPath() const;

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl;  // PIMPL idiom for libisofs encapsulation
};

#endif // ISOCORE_H
