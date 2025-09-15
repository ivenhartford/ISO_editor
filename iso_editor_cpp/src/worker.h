#ifndef WORKER_H
#define WORKER_H

#include <QObject>
#include "iso_core.h"

class Worker : public QObject
{
    Q_OBJECT

public:
    explicit Worker(QObject *parent = nullptr);
    ~Worker();

public slots:
    void doLoadIso(const QString& filePath);
    void doSaveIso(const QString& filePath, bool useUdf, bool makeHybrid);

signals:
    void loadFinished(bool success, const IsoNode* tree, const VolumeDescriptor& vd, bool isCueSheet);
    void saveFinished(bool success, const QString& message);

private:
    ISOCore m_core;
};

#endif // WORKER_H
