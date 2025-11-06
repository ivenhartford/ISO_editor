#ifndef PROPERTIESDIALOG_H
#define PROPERTIESDIALOG_H

#include <QDialog>
#include <QLineEdit>
#include <QComboBox>
#include <QPushButton>
#include <QDialogButtonBox>
#include <QString>
#include <QMap>

// Forward declaration
class ISOCore;

/**
 * @brief Dialog for editing ISO properties
 *
 * This dialog allows the user to:
 * - Edit volume ID and system ID
 * - View detected boot information (read-only)
 * - Configure BIOS boot image
 * - Configure EFI boot image
 * - Select boot emulation type
 */
class PropertiesDialog : public QDialog {
    Q_OBJECT

public:
    /**
     * @brief Constructs a PropertiesDialog
     * @param core Pointer to the ISOCore instance
     * @param parent Parent widget (optional)
     */
    explicit PropertiesDialog(ISOCore* core, QWidget* parent = nullptr);

    /**
     * @brief Gets the volume ID entered by the user
     * @return Volume ID string
     */
    QString getVolumeId() const;

    /**
     * @brief Gets the system ID entered by the user
     * @return System ID string
     */
    QString getSystemId() const;

    /**
     * @brief Gets the BIOS boot image path
     * @return Path to BIOS boot image
     */
    QString getBootImagePath() const;

    /**
     * @brief Gets the EFI boot image path
     * @return Path to EFI boot image
     */
    QString getEfiBootImagePath() const;

    /**
     * @brief Gets the selected boot emulation type
     * @return Emulation type (noemul, floppy, hdemul)
     */
    QString getEmulationType() const;

public slots:
    /**
     * @brief Validates input and accepts the dialog
     *
     * Performs validation on:
     * - Volume ID length and content
     * - System ID length
     * - Boot image paths (if provided)
     */
    void accept() override;

private slots:
    /**
     * @brief Opens file dialog to browse for boot images
     * @param lineEdit The QLineEdit to update with selected path
     * @param title Dialog title
     */
    void browseForImage(QLineEdit* lineEdit, const QString& title);

private:
    /**
     * @brief Sets up the UI layout
     * @param core Pointer to ISOCore for initial values
     */
    void setupUi(ISOCore* core);

    /**
     * @brief Validates boot image file path
     * @param path Path to boot image
     * @return true if valid, false otherwise
     */
    bool validateBootImagePath(const QString& path) const;

    // UI Components
    QLineEdit* volumeIdEdit;
    QLineEdit* systemIdEdit;
    QLineEdit* bootImageEdit;
    QLineEdit* efiBootImageEdit;
    QComboBox* emulationCombo;
    QDialogButtonBox* buttonBox;
};

#endif // PROPERTIESDIALOG_H
