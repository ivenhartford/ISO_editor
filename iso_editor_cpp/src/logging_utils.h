#ifndef LOGGING_UTILS_H
#define LOGGING_UTILS_H

enum LogLevel {
    LogLevelDebug,
    LogLevelInfo,
    LogLevelWarning,
    LogLevelCritical,
    LogLevelFatal
};

void setupLogging();

#endif // LOGGING_UTILS_H
