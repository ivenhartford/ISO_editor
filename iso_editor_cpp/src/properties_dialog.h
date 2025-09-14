#ifndef PROPERTIESDIALOG_H
#define PROPERTIESDIALOG_H

#include <QDialog>
#include <QString>

// Forward declarations
class QLineEdit;
class QDialogButtonBox;

struct IsoProperties {
    QString volumeId;
    QString systemId;
    QString bootImagePath;
    QString efiBootImagePath;
};

class PropertiesDialog : public QDialog
{
    Q_OBJECT

public:
    explicit PropertiesDialog(const IsoProperties &initialProps, QWidget *parent = nullptr);

    IsoProperties getProperties() const;

private slots:
    void browseForBiosImage();
    void browseForEfiImage();

private:
    void browseForImage(QLineEdit *lineEdit, const QString &title);

    QLineEdit *volumeIdEdit;
    QLineEdit *systemIdEdit;
    QLineEdit *bootImageEdit;
    QLineEdit *efiBootImageEdit;
    QDialogButtonBox *buttonBox;
};

#endif // PROPERTIESDIALOG_H
