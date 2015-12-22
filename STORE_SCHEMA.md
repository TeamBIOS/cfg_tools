# Описание таблиц до 8.3

## objects - Объекты метаданных

1. OBJID - ID объекта
1. CLASSID - Класс метаданных
1. PARENTID - Родитель, для вложенных объектов
1. SELFVERNUM - Своя версия
1. REVISED - Захвачен
1. REVISORID - Кто захватил
1. REVISEDATE - Когда захватил

## depot
1. DEPOTID
1. ROOTOBJID
1. CREATEDATE
1. DEPOTVER

## selfrefs
1. OBJID
1. VERNUM
1. OBJREF

## history - История изменений обьъектов
1. OBJID - ID объекта
1. VERNUM - Номер версии
1. SELFVERNUM - Своя версия
1. OBJVERID - ID версии
1. OWNERID - Владелец
1. OBJNAME - Имя объекта, на момент помещения
1. OBJPOS - ??
1. REMOVED - ??
1. DATAPACKED - Упакован, deflate?
1. OBJDATA - Данные версии объекта

## lastestversions - Срез последних версий объектов
1. OBJID - ID объекта
1. VERNUM - Номер версии

## labels - Метки
1. VERNUM - Версия
1. USERID - Пользователь?
1. LABELDATE - Дата создания?
1. NAME - Имя метки
1. COMMENT - Комментарий

## users - Пользователи хранилища
1. USERID - ID пользователя
1. NAME - Имя
1. PASSWORD - Пароль?
1. REMOVED - Удален
1. BINDID - Привязан к хранилищу
1. BINDSTRING - Строка подключения базы(которая подкл. к хранилищу)
1. RIGHTS - Права?

## outrefs
1. OBJID
1. VERNUM
1. OBJREF

## versions - Версии объектов
1. VERNUM - Номер версии
1. USERID - Пользователь, поместивший
1. VERDATE - Дата версии
1. CODE - ?
1. COMMENT - Комментарий
1. SNAPSHOTMAKER - ID снапшота
1. SNAPSHOTCRC - Контрольная сумма

## externals - Файлы сложных объектов(модули, формы и тд)
1. OBJID - ID объекта(владельца файлов)
1. VERNUM - Версия
1. EXTNAME - Имя файла(ID объекта + расширение)
1. EXTVERID - ?
1. DATAPACKED - Данные упакованы, deflate
1. EXTDATA - Данные


# Изменения для 8.3

## depot
1. DEPOTID
1. ROOTOBJID
1. CREATEDATE
1. DEPOTVER
1. COMPATIBILITYMODE

## outrefs
1. OBJID
1. VERNUM
1. OBJREF
1. KIND

## objects
1. OBJID
1. CLASSID
1. SELFVERNUM
1. REVISED
1. REVISORID
1. REVISEDATE

## history
1. OBJID
1. VERNUM
1. SELFVERNUM
1. OBJVERID
1. PARENTID
1. OWNERID
1. OBJNAME
1. OBJPOS
1. REMOVED
1. DATAPACKED
1. OBJDATA
1. DATAHASH

## versions
1. VERNUM
1. USERID
1. VERDATE
1. PVERSION
1. CVERSION
1. CODE
1. COMMENT
1. SNAPSHOTMAKER
1. SNAPSHOTCRC
1. VERSIONID

## externals
1. OBJID
1. VERNUM
1. EXTNAME
1. EXTVERID
1. DATAPACKED
1. EXTDATA
1. DATAHASH