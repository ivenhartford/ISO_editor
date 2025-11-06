#include "dialogs/PropertiesDialog.h"
#include "core/ISOCore.h"
#include "Constants.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QGroupBox>
#include <QLabel>
#include <QFileDialog>
#include <QMessageBox>
#include <QFileInfo>

PropertiesDialog::PropertiesDialog(ISOCore* core, QWidget* parent)
    : QDialog(parent)
    , volumeIdEdit(nullptr)
    , systemIdEdit(nullptr)
    , bootImageEdit(nullptr)
    , efiBootImageEdit(nullptr)
    , emulationCombo(nullptr)
    , buttonBox(nullptr)
{
    setWindowTitle("ISO Properties");
    setMinimumWidth(500);
    setupUi(core);
}

void PropertiesDialog::setupUi(ISOCore* core) {
    auto* mainLayout = new QVBoxLayout(this);

    // Volume Properties Group
    auto* volumeGroup = new QGroupBox("Volume Properties", this);
    auto* volumeLayout = new QFormLayout();

    volumeIdEdit = new QLineEdit(core->getVolumeId(), this);
    volumeIdEdit->setToolTip(
        QString("ISO volume label (max %1 characters)")
            .arg(Constants::MAX_VOLUME_ID_LENGTH)
    );
    volumeIdEdit->setMaxLength(Constants::MAX_VOLUME_ID_LENGTH);

    systemIdEdit = new QLineEdit(core->getSystemId(), this);
    systemIdEdit->setToolTip(
        QString("System identifier (max %1 characters)")
            .arg(Constants::MAX_SYSTEM_ID_LENGTH)
    );
    systemIdEdit->setMaxLength(Constants::MAX_SYSTEM_ID_LENGTH);

    volumeLayout->addRow("Volume ID:", volumeIdEdit);
    volumeLayout->addRow("System ID:", systemIdEdit);
    volumeGroup->setLayout(volumeLayout);
    mainLayout->addWidget(volumeGroup);

    // Detected Boot Info Group (Read-only)
    const auto& bootInfo = core->getExtractedBootInfo();
    if (!bootInfo.isEmpty()) {
        auto* detectedBootGroup = new QGroupBox("Detected Boot Information", this);
        auto* detectedBootLayout = new QFormLayout();

        // Map platform IDs to strings
        QMap<uint8_t, QString> platformMap = {
            {Constants::BOOT_PLATFORM_X86, "x86"},
            {Constants::BOOT_PLATFORM_POWERPC, "PowerPC"},
            {Constants::BOOT_PLATFORM_MAC, "Mac"},
            {Constants::BOOT_PLATFORM_EFI, "EFI"}
        };

        const auto& firstBootEntry = bootInfo.first();
        uint8_t platformId = firstBootEntry.value("platform_id", 0);
        QString platformStr = platformMap.value(platformId, "Unknown");

        detectedBootLayout->addRow(new QLabel("Platform:"),
                                   new QLabel(platformStr));
        detectedBootLayout->addRow(new QLabel("Emulation:"),
                                   new QLabel(firstBootEntry.value("emulation_type", "N/A")));
        detectedBootLayout->addRow(new QLabel("Boot Image:"),
                                   new QLabel(firstBootEntry.value("boot_image_path", "N/A")));

        detectedBootGroup->setLayout(detectedBootLayout);
        mainLayout->addWidget(detectedBootGroup);
    }

    // Boot Options Group (Editable)
    auto* bootGroup = new QGroupBox("Boot Options", this);
    auto* bootFormLayout = new QFormLayout();

    // BIOS Boot Image
    bootImageEdit = new QLineEdit(core->getBootImagePath(), this);
    bootImageEdit->setPlaceholderText("Path to BIOS boot image (.img, .bin)...");
    bootImageEdit->setToolTip("El Torito boot image for BIOS systems (typically boot.img)");

    auto* biosBrowseButton = new QPushButton("Browse...", this);
    biosBrowseButton->setToolTip("Browse for BIOS boot image file");
    connect(biosBrowseButton, &QPushButton::clicked, this, [this]() {
        browseForImage(bootImageEdit, "Select BIOS Boot Image");
    });

    auto* biosBootLayout = new QHBoxLayout();
    biosBootLayout->addWidget(bootImageEdit);
    biosBootLayout->addWidget(biosBrowseButton);
    bootFormLayout->addRow("BIOS Boot Image:", biosBootLayout);

    // Emulation Type
    emulationCombo = new QComboBox(this);
    emulationCombo->addItems({
        Constants::BOOT_EMULATION_NOEMUL,
        Constants::BOOT_EMULATION_FLOPPY,
        Constants::BOOT_EMULATION_HDEMUL
    });
    emulationCombo->setToolTip(
        "Boot emulation mode:\n"
        "• noemul: No emulation (recommended)\n"
        "• floppy: Floppy disk emulation\n"
        "• hdemul: Hard disk emulation"
    );

    QString currentEmulation = core->getBootEmulationType();
    if (currentEmulation.isEmpty()) {
        currentEmulation = Constants::BOOT_EMULATION_NOEMUL;
    }
    emulationCombo->setCurrentText(currentEmulation);
    bootFormLayout->addRow("Emulation Type:", emulationCombo);

    // EFI Boot Image
    efiBootImageEdit = new QLineEdit(core->getEfiBootImagePath(), this);
    efiBootImageEdit->setPlaceholderText("Path to EFI boot image...");
    efiBootImageEdit->setToolTip("EFI boot image for UEFI systems (typically efiboot.img)");

    auto* efiBrowseButton = new QPushButton("Browse...", this);
    efiBrowseButton->setToolTip("Browse for EFI boot image file");
    connect(efiBrowseButton, &QPushButton::clicked, this, [this]() {
        browseForImage(efiBootImageEdit, "Select EFI Boot Image");
    });

    auto* efiBootLayout = new QHBoxLayout();
    efiBootLayout->addWidget(efiBootImageEdit);
    efiBootLayout->addWidget(efiBrowseButton);
    bootFormLayout->addRow("EFI Boot Image:", efiBootLayout);

    bootGroup->setLayout(bootFormLayout);
    mainLayout->addWidget(bootGroup);

    // Dialog Buttons
    buttonBox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel,
        this
    );
    connect(buttonBox, &QDialogButtonBox::accepted, this, &PropertiesDialog::accept);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &PropertiesDialog::reject);
    mainLayout->addWidget(buttonBox);
}

void PropertiesDialog::browseForImage(QLineEdit* lineEdit, const QString& title) {
    QString filePath = QFileDialog::getOpenFileName(
        this,
        title,
        QString(),
        Constants::BOOT_IMAGE_FILTER
    );

    if (!filePath.isEmpty()) {
        lineEdit->setText(filePath);
    }
}

bool PropertiesDialog::validateBootImagePath(const QString& path) const {
    if (path.isEmpty()) {
        return true; // Empty path is valid (optional boot image)
    }

    QFileInfo fileInfo(path);
    if (!fileInfo.exists()) {
        return false;
    }

    if (!fileInfo.isFile()) {
        return false;
    }

    // Check file extension
    QString ext = fileInfo.suffix().toLower();
    if (ext != "img" && ext != "bin") {
        return false;
    }

    return true;
}

void PropertiesDialog::accept() {
    // Validate volume ID
    QString volumeId = volumeIdEdit->text().trimmed();
    if (volumeId.isEmpty()) {
        QMessageBox::warning(
            this,
            "Invalid Input",
            "Volume ID cannot be empty."
        );
        return;
    }

    if (volumeId.length() > Constants::MAX_VOLUME_ID_LENGTH) {
        QMessageBox::warning(
            this,
            "Invalid Input",
            QString("Volume ID must be %1 characters or less.")
                .arg(Constants::MAX_VOLUME_ID_LENGTH)
        );
        return;
    }

    // Validate system ID
    QString systemId = systemIdEdit->text().trimmed();
    if (systemId.length() > Constants::MAX_SYSTEM_ID_LENGTH) {
        QMessageBox::warning(
            this,
            "Invalid Input",
            QString("System ID must be %1 characters or less.")
                .arg(Constants::MAX_SYSTEM_ID_LENGTH)
        );
        return;
    }

    // Validate boot image paths if provided
    QString bootPath = bootImageEdit->text().trimmed();
    if (!validateBootImagePath(bootPath)) {
        QMessageBox::warning(
            this,
            "Invalid Boot Image",
            QString("The BIOS boot image file does not exist or is invalid:\n%1")
                .arg(bootPath)
        );
        return;
    }

    QString efiPath = efiBootImageEdit->text().trimmed();
    if (!validateBootImagePath(efiPath)) {
        QMessageBox::warning(
            this,
            "Invalid Boot Image",
            QString("The EFI boot image file does not exist or is invalid:\n%1")
                .arg(efiPath)
        );
        return;
    }

    // All validation passed
    QDialog::accept();
}

// Getters
QString PropertiesDialog::getVolumeId() const {
    return volumeIdEdit->text().trimmed();
}

QString PropertiesDialog::getSystemId() const {
    return systemIdEdit->text().trimmed();
}

QString PropertiesDialog::getBootImagePath() const {
    return bootImageEdit->text().trimmed();
}

QString PropertiesDialog::getEfiBootImagePath() const {
    return efiBootImageEdit->text().trimmed();
}

QString PropertiesDialog::getEmulationType() const {
    return emulationCombo->currentText();
}
