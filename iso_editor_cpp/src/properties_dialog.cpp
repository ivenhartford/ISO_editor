#include "properties_dialog.h"

#include <QVBoxLayout>
#include <QFormLayout>
#include <QGroupBox>
#include <QLineEdit>
#include <QPushButton>
#include <QDialogButtonBox>
#include <QFileDialog>

PropertiesDialog::PropertiesDialog(const IsoProperties &initialProps, QWidget *parent)
    : QDialog(parent)
{
    setWindowTitle("ISO Properties");
    auto *mainLayout = new QFormLayout(this);

    // Volume Properties
    auto *volumeGroup = new QGroupBox("Volume Properties");
    auto *volumeLayout = new QFormLayout(volumeGroup);
    volumeIdEdit = new QLineEdit(initialProps.volumeId, this);
    systemIdEdit = new QLineEdit(initialProps.systemId, this);
    volumeLayout->addRow("Volume ID:", volumeIdEdit);
    volumeLayout->addRow("System ID:", systemIdEdit);
    mainLayout->addRow(volumeGroup);

    // Boot Properties
    auto *bootGroup = new QGroupBox("Boot Options");
    auto *bootFormLayout = new QFormLayout(bootGroup);

    // BIOS Boot Image
    bootImageEdit = new QLineEdit(initialProps.bootImagePath, this);
    auto *biosBrowseButton = new QPushButton("Browse...", this);
    connect(biosBrowseButton, &QPushButton::clicked, this, &PropertiesDialog::browseForBiosImage);
    auto *biosBootLayout = new QHBoxLayout();
    biosBootLayout->addWidget(bootImageEdit);
    biosBootLayout->addWidget(biosBrowseButton);
    bootFormLayout->addRow("BIOS Boot Image:", biosBootLayout);

    // EFI Boot Image
    efiBootImageEdit = new QLineEdit(initialProps.efiBootImagePath, this);
    auto *efiBrowseButton = new QPushButton("Browse...", this);
    connect(efiBrowseButton, &QPushButton::clicked, this, &PropertiesDialog::browseForEfiImage);
    auto *efiBootLayout = new QHBoxLayout();
    efiBootLayout->addWidget(efiBootImageEdit);
    efiBootLayout->addWidget(efiBrowseButton);
    bootFormLayout->addRow("EFI Boot Image:", efiBootLayout);
    mainLayout->addRow(bootGroup);

    // Dialog Buttons
    buttonBox = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, this);
    connect(buttonBox, &QDialogButtonBox::accepted, this, &QDialog::accept);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
    mainLayout->addRow(buttonBox);
}

IsoProperties PropertiesDialog::getProperties() const
{
    return {
        volumeIdEdit->text(),
        systemIdEdit->text(),
        bootImageEdit->text(),
        efiBootImageEdit->text()
    };
}

void PropertiesDialog::browseForBiosImage()
{
    browseForImage(bootImageEdit, "Select BIOS Boot Image");
}

void PropertiesDialog::browseForEfiImage()
{
    browseForImage(efiBootImageEdit, "Select EFI Boot Image");
}

void PropertiesDialog::browseForImage(QLineEdit *lineEdit, const QString &title)
{
    QString filePath = QFileDialog::getOpenFileName(this, title, "", "Boot Images (*.img *.bin);;All Files (*)");
    if (!filePath.isEmpty()) {
        lineEdit->setText(filePath);
    }
}
