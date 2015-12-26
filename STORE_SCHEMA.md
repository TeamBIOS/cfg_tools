# Описание таблиц до 8.3

## OBJECTS - Объекты метаданных

1. **OBJID** [GUID] - ID объекта
1. **CLASSID** [GUID] - Класс метаданных
1. **PARENTID** [GUID] - Родитель, для вложенных объектов
1. **SELFVERNUM** [N(10)] - Своя версия
1. **REVISED** [BOOL NULLABLE] - Захвачен
1. **REVISORID** [GUID NULLABLE] - Кто захватил
1. **REVISEDATE** [DATE NULLABLE] - Когда захватил

## DEPOT
1. **DEPOTID** [GUID]
1. **ROOTOBJID** [GUID]
1. **CREATEDATE** [DATE]
1. **DEPOTVER** [B(8)]

## SELFREFS
1. **OBJID** [GUID]
1. **VERNUM** [N(10)]
1. **OBJREF** [GUID]

## HISTORY - История изменений обьъектов
1. **OBJID** [GUID] - ID объекта
1. **VERNUM** [N(10)] - Номер версии
1. **SELFVERNUM** [N(10)] - Своя версия
1. **OBJVERID** [GUID] - ID версии
1. **OWNERID** [GUID NULLABLE] - Владелец
1. **OBJNAME** [NVC(256)] - Имя объекта, на момент помещения
1. **OBJPOS** [N(6)] - ??
1. **REMOVED** [BOOL] - ??
1. **DATAPACKED** [BOOL NULLABLE] - Упакован, deflate?
1. **OBJDATA** [I(0) NULLABLE] - Данные версии объекта

## LASTESTVERSIONS - Срез последних версий объектов
1. **OBJID** [GUID] - ID объекта
1. **VERNUM** [N(10)] - Номер версии

## LABELS - Метки
1. **VERNUM** [N(10)] - Версия
1. **USERID** [GUID] - Пользователь?
1. **LABELDATE** [DATE] - Дата создания?
1. **NAME** [NVC(256)] - Имя метки
1. **COMMENT** [NT(0) NULLABLE] - Комментарий

## USERS - Пользователи хранилища
1. **USERID** [GUID] - ID пользователя
1. **NAME** [NVC(256)] - Имя
1. **PASSWORD** [NC(32)] - Пароль?
1. **REMOVED** [BOOL] - Удален
1. **BINDID** [GUID NULLABLE] - Привязан к хранилищу
1. **BINDSTRING** [NT(0) NULLABLE] - Строка подключения базы(которая подкл. к хранилищу)
1. **RIGHTS** [B(4)] - Права?

## OUTREFS
1. **OBJID** [GUID]
1. **VERNUM** [N(10)]
1. **OBJREF** [GUID]

## VERSIONS - Версии объектов
1. **VERNUM** [N(10)] - Номер версии
1. **USERID** [GUID] - Пользователь, поместивший
1. **VERDATE** [DATE] - Дата версии
1. **CODE** [NVC(256) NULLABLE] - ?
1. **COMMENT** [NT(0) NULLABLE] - Комментарий
1. **SNAPSHOTMAKER** [GUID NULLABLE] - ID снапшота
1. **SNAPSHOTCRC** [B(4) NULLABLE] - Контрольная сумма

## EXTERNALS - Файлы сложных объектов(модули, формы и тд)
1. **OBJID** [GUID] - ID объекта(владельца файлов)
1. **VERNUM** [N(10)] - Версия
1. **EXTNAME** [NVC(128)] - Имя файла(ID объекта + расширение)
1. **EXTVERID** [GUID] - ?
1. **DATAPACKED** [BOOL] - Данные упакованы, deflate
1. **EXTDATA** [I(0)] - Данные


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