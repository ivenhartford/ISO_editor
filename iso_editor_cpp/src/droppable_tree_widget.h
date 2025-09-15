#ifndef DROPPABLETREEWIDGET_H
#define DROPPABLETREEWIDGET_H

#include <QTreeWidget>
#include <QStringList>

class DroppableTreeWidget : public QTreeWidget
{
    Q_OBJECT

public:
    explicit DroppableTreeWidget(QWidget *parent = nullptr);

signals:
    void filesDropped(const QStringList &filePaths);

protected:
    void dragEnterEvent(QDragEnterEvent *event) override;
    void dragMoveEvent(QDragMoveEvent *event) override;
    void dropEvent(QDropEvent *event) override;
};

#endif // DROPPABLETREEWIDGET_H
