#include "droppable_tree_widget.h"
#include <QDragEnterEvent>
#include <QMimeData>
#include <QUrl>

DroppableTreeWidget::DroppableTreeWidget(QWidget *parent)
    : QTreeWidget(parent)
{
    setAcceptDrops(true);
}

void DroppableTreeWidget::dragEnterEvent(QDragEnterEvent *event)
{
    if (event->mimeData()->hasUrls()) {
        event->acceptProposedAction();
    } else {
        QTreeWidget::dragEnterEvent(event);
    }
}

void DroppableTreeWidget::dragMoveEvent(QDragMoveEvent *event)
{
    if (event->mimeData()->hasUrls()) {
        event->acceptProposedAction();
    } else {
        QTreeWidget::dragMoveEvent(event);
    }
}

void DroppableTreeWidget::dropEvent(QDropEvent *event)
{
    if (event->mimeData()->hasUrls()) {
        QStringList filePaths;
        for (const QUrl &url : event->mimeData()->urls()) {
            filePaths.append(url.toLocalFile());
        }
        if (!filePaths.isEmpty()) {
            emit filesDropped(filePaths);
        }
        event->acceptProposedAction();
    } else {
        QTreeWidget::dropEvent(event);
    }
}
