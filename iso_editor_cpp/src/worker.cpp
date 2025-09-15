#include "worker.h"

Worker::Worker(QObject *parent)
    : QObject{parent}
{
}

Worker::~Worker()
{
}

#include <QFileInfo>

void Worker::doLoadIso(const QString& filePath)
{
    bool success = m_core.loadIso(filePath);
    QFileInfo fileInfo(filePath);
    bool isCue = fileInfo.suffix().compare("cue", Qt::CaseInsensitive) == 0;

    emit loadFinished(success, m_core.getDirectoryTree(), m_core.getVolumeDescriptor(), isCue);
}

void Worker::doSaveIso(const QString& filePath, bool useUdf, bool makeHybrid)
{
    bool success = m_core.saveIso(filePath, useUdf, makeHybrid);
    QString message = success ? "ISO saved successfully." : "Failed to save ISO.";
    emit saveFinished(success, message);
}
