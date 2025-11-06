#include "core/ISOCore.h"
#include <QDebug>

/**
 * @brief Private implementation (PIMPL idiom)
 *
 * This hides libisofs implementation details from the header,
 * reducing compile dependencies and improving encapsulation.
 */
struct ISOCore::Impl {
    QString currentIsoPath;
    QString volumeId;
    QString systemId;
    QString bootImagePath;
    QString efiBootImagePath;
    QString bootEmulationType;
    uint64_t volumeSize;
    bool modified;
    bool loaded;
    QList<QMap<QString, QVariant>> extractedBootInfo;

    // libisofs structures (to be implemented)
    // IsoImage* isoImage;
    // IsoWriteOpts* writeOpts;

    Impl()
        : volumeId("NEW_ISO")
        , systemId("TK_ISO_EDITOR")
        , bootEmulationType("noemul")
        , volumeSize(0)
        , modified(false)
        , loaded(false)
    {
    }
};

ISOCore::ISOCore()
    : pImpl(std::make_unique<Impl>())
{
    qDebug() << "ISOCore initialized";
}

ISOCore::~ISOCore() {
    closeIso();
}

void ISOCore::initNewIso() {
    qDebug() << "Initializing new ISO";
    closeIso();

    pImpl->currentIsoPath.clear();
    pImpl->volumeId = "NEW_ISO";
    pImpl->systemId = "TK_ISO_EDITOR";
    pImpl->bootImagePath.clear();
    pImpl->efiBootImagePath.clear();
    pImpl->bootEmulationType = "noemul";
    pImpl->volumeSize = 0;
    pImpl->modified = false;
    pImpl->loaded = false;
    pImpl->extractedBootInfo.clear();

    // TODO: Initialize libisofs structures
    // iso_image_new(pImpl->volumeId.toLocal8Bit().data(), &pImpl->isoImage);
}

bool ISOCore::loadIso(const QString& filePath) {
    qDebug() << "Loading ISO:" << filePath;

    // TODO: Implement actual ISO loading with libisofs
    // For now, this is a stub that simulates loading

    pImpl->currentIsoPath = filePath;
    pImpl->loaded = true;
    pImpl->modified = false;

    // Simulate reading volume descriptor
    pImpl->volumeId = "LOADED_ISO";
    pImpl->systemId = "LINUX";
    pImpl->volumeSize = 4700 * 1024 * 1024; // 4.7 GB

    return true;
}

bool ISOCore::saveIso(const QString& filePath, const QMap<QString, QVariant>& options) {
    qDebug() << "Saving ISO to:" << filePath << "with options:" << options;

    // TODO: Implement actual ISO saving with libisofs/libisoburn

    pImpl->currentIsoPath = filePath;
    pImpl->modified = false;

    return true;
}

void ISOCore::closeIso() {
    if (pImpl->loaded) {
        qDebug() << "Closing ISO:" << pImpl->currentIsoPath;

        // TODO: Clean up libisofs structures
        // if (pImpl->isoImage) {
        //     iso_image_unref(pImpl->isoImage);
        //     pImpl->isoImage = nullptr;
        // }

        pImpl->loaded = false;
    }
}

// Getters and Setters

QString ISOCore::getVolumeId() const {
    return pImpl->volumeId;
}

void ISOCore::setVolumeId(const QString& volumeId) {
    pImpl->volumeId = volumeId;
    pImpl->modified = true;
}

QString ISOCore::getSystemId() const {
    return pImpl->systemId;
}

void ISOCore::setSystemId(const QString& systemId) {
    pImpl->systemId = systemId;
    pImpl->modified = true;
}

uint64_t ISOCore::getVolumeSize() const {
    return pImpl->volumeSize;
}

QString ISOCore::getBootImagePath() const {
    return pImpl->bootImagePath;
}

void ISOCore::setBootImagePath(const QString& path) {
    pImpl->bootImagePath = path;
    pImpl->modified = true;
}

QString ISOCore::getEfiBootImagePath() const {
    return pImpl->efiBootImagePath;
}

void ISOCore::setEfiBootImagePath(const QString& path) {
    pImpl->efiBootImagePath = path;
    pImpl->modified = true;
}

QString ISOCore::getBootEmulationType() const {
    return pImpl->bootEmulationType;
}

void ISOCore::setBootEmulationType(const QString& type) {
    pImpl->bootEmulationType = type;
    pImpl->modified = true;
}

QList<QMap<QString, QVariant>> ISOCore::getExtractedBootInfo() const {
    return pImpl->extractedBootInfo;
}

// File/Directory Operations (stubs)

bool ISOCore::addFile(const QString& hostPath, const QString& isoPath) {
    qDebug() << "Adding file:" << hostPath << "to ISO path:" << isoPath;
    // TODO: Implement with libisofs
    pImpl->modified = true;
    return true;
}

bool ISOCore::addDirectory(const QString& hostPath, const QString& isoPath, bool recursive) {
    qDebug() << "Adding directory:" << hostPath << "to ISO path:" << isoPath
             << "(recursive:" << recursive << ")";
    // TODO: Implement with libisofs
    pImpl->modified = true;
    return true;
}

bool ISOCore::removeNode(const QString& isoPath) {
    qDebug() << "Removing node:" << isoPath;
    // TODO: Implement with libisofs
    pImpl->modified = true;
    return true;
}

bool ISOCore::createDirectory(const QString& isoPath) {
    qDebug() << "Creating directory:" << isoPath;
    // TODO: Implement with libisofs
    pImpl->modified = true;
    return true;
}

// State queries

bool ISOCore::isModified() const {
    return pImpl->modified;
}

void ISOCore::setModified(bool modified) {
    pImpl->modified = modified;
}

bool ISOCore::isLoaded() const {
    return pImpl->loaded;
}

QString ISOCore::getCurrentIsoPath() const {
    return pImpl->currentIsoPath;
}
