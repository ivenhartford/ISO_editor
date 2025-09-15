#include "logging_utils.h"
#include <QFile>
#include <QTextStream>
#include <QDateTime>
#include <QDebug>
#include <iostream>
#include <QString>

// --- Configuration ---
const QString LOG_FILE_PATH = "iso_editor.log";
const LogLevel LOG_LEVEL = LogLevelInfo;
// ---------------------

static QFile logFile;

void customMessageHandler(QtMsgType type, const QMessageLogContext &context, const QString &msg)
{
    LogLevel msgLogLevel;
    switch (type) {
    case QtDebugMsg:
        msgLogLevel = LogLevelDebug;
        break;
    case QtInfoMsg:
        msgLogLevel = LogLevelInfo;
        break;
    case QtWarningMsg:
        msgLogLevel = LogLevelWarning;
        break;
    case QtCriticalMsg:
        msgLogLevel = LogLevelCritical;
        break;
    case QtFatalMsg:
        msgLogLevel = LogLevelFatal;
        break;
    }

    if (msgLogLevel < LOG_LEVEL) {
        return;
    }

    QString formattedMsg;
    QTextStream stream(&formattedMsg);
    stream << QDateTime::currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz") << " ";

    switch (type) {
    case QtDebugMsg:
        stream << "[DEBUG]";
        break;
    case QtInfoMsg:
        stream << "[INFO]";
        break;
    case QtWarningMsg:
        stream << "[WARNING]";
        break;
    case QtCriticalMsg:
        stream << "[CRITICAL]";
        break;
    case QtFatalMsg:
        stream << "[FATAL]";
        break;
    }

    stream << " " << msg;
    if (context.file) {
        stream << " (" << context.file << ":" << context.line << ", " << context.function << ")";
    }

    // Print to console
    std::cerr << formattedMsg.toStdString() << std::endl;

    // Write to log file
    if (logFile.isOpen()) {
        QTextStream logStream(&logFile);
        logStream << formattedMsg << "\n";
        logStream.flush();
    }
}

void setupLogging()
{
    logFile.setFileName(LOG_FILE_PATH);
    // Open in append mode, so we don't overwrite previous logs on each start
    if (logFile.open(QIODevice::WriteOnly | QIODevice::Append | QIODevice::Text)) {
        qInstallMessageHandler(customMessageHandler);
        qInfo() << "=================================================";
        qInfo() << "Application starting, logging initialized.";
        qInfo() << "=================================================";
    } else {
        qWarning() << "Failed to open log file for writing:" << logFile.errorString();
    }
}
