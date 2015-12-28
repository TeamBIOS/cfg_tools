# Описание таблиц до 8.3

## OBJECTS - Объекты метаданных

1. **OBJID** [GUID] - ID объекта
1. **CLASSID** [GUID] - Класс метаданных
1. <span style='color: red'><b>PARENTID</b> [GUID] - Родитель, для вложенных объектов</span>
1. **SELFVERNUM** [Numeric(10)] - Своя версия
1. **REVISED** [BOOL NULLABLE] - Захвачен
1. **REVISORID** [GUID NULLABLE] - Кто захватил
1. **REVISEDATE** [DATE NULLABLE] - Когда захватил

## DEPOT
1. **DEPOTID** [GUID]
1. **ROOTOBJID** [GUID]
1. **CREATEDATE** [DATE]
1. **DEPOTVER** [BYTE(8)]

## SELFREFS
1. **OBJID** [GUID]
1. **VERNUM** [Numeric(10)]
1. **OBJREF** [GUID]

## HISTORY - История изменений обьъектов
1. **OBJID** [GUID] - ID объекта
1. **VERNUM** [Numeric(10)] - Номер версии
1. **SELFVERNUM** [Numeric(10)] - Своя версия
1. **OBJVERID** [GUID] - ID версии
1. **OWNERID** [GUID NULLABLE] - Владелец
1. **OBJNAME** [String(256)] - Имя объекта, на момент помещения
1. **OBJPOS** [Numeric(6)] - ??
1. **REMOVED** [BOOL] - ??
1. **DATAPACKED** [BOOL NULLABLE] - Упакован, deflate?
1. **OBJDATA** [BYTE(0) NULLABLE] - Данные версии объекта

## LASTESTVERSIONS - Срез последних версий объектов
1. **OBJID** [GUID] - ID объекта
1. **VERNUM** [Numeric(10)] - Номер версии

## LABELS - Метки
1. **VERNUM** [Numeric(10)] - Версия
1. **USERID** [GUID] - Пользователь?
1. **LABELDATE** [DATE] - Дата создания?
1. **NAME** [String(256)] - Имя метки
1. **COMMENT** [String(0) NULLABLE] - Комментарий

## USERS - Пользователи хранилища
1. **USERID** [GUID] - ID пользователя
1. **NAME** [String(256)] - Имя
1. **PASSWORD** [String(32)] - Пароль?
1. **REMOVED** [BOOL] - Удален
1. **BINDID** [GUID NULLABLE] - Привязан к хранилищу
1. **BINDSTRING** [String(0) NULLABLE] - Строка подключения базы(которая подкл. к хранилищу)
1. **RIGHTS** [BYTE(4)] - Права?

## OUTREFS
1. **OBJID** [GUID]
1. **VERNUM** [Numeric(10)]
1. **OBJREF** [GUID]

## VERSIONS - Версии объектов
1. **VERNUM** [Numeric(10)] - Номер версии
1. **USERID** [GUID] - Пользователь, поместивший
1. **VERDATE** [DATE] - Дата версии
1. **CODE** [String(256) NULLABLE] - ?
1. **COMMENT** [String(0) NULLABLE] - Комментарий
1. **SNAPSHOTMAKER** [GUID NULLABLE] - ID снапшота
1. **SNAPSHOTCRC** [BYTE(4) NULLABLE] - Контрольная сумма

## EXTERNALS - Файлы сложных объектов(модули, формы и тд)
1. **OBJID** [GUID] - ID объекта(владельца файлов)
1. **VERNUM** [Numeric(10)] - Версия
1. **EXTNAME** [String(128)] - Имя файла(ID объекта + расширение)
1. **EXTVERID** [GUID] - ?
1. **DATAPACKED** [BOOL] - Данные упакованы, deflate
1. **EXTDATA** [BYTE(0)] - Данные


# Изменения для 8.3

## DEPOT
1. **DEPOTID** [GUID]
1. **ROOTOBJID** [GUID]
1. **CREATEDATE** [DateTime]
1. **DEPOTVER** [BYTE(8)]
1. <span style='color: green'><b>COMPATIBILITYMODE</b></span> [Numeric(10)]

## OUTREFS
1. **OBJID** [GUID]
1. **VERNUM** [Numeric(10)]
1. **OBJREF** [GUID]
1. <span style='color: green'><b>KIND</b> [Numeric(1)]</span>

## OBJECTS
1. **OBJID** [GUID]
1. **CLASSID** [GUID]
1. **SELFVERNUM** [Numeric(10)]
1. **REVISED** [BOOL NULLABLE]
1. **REVISORID** [GUID NULLABLE]
1. **REVISEDATE** [DateTime NULLABLE]

## HISTORY
1. **OBJID** [GUID]
1. **VERNUM** [Numeric(10)]
1. **SELFVERNUM** [Numeric(10)]
1. **OBJVERID** [GUID]
1. <span style='color: green'><b>PARENTID</b> [GUID]</span>
1. **OWNERID** [GUID NULLABLE]
1. **OBJNAME** [String(256)]
1. **OBJPOS** [Numeric(6)]
1. **REMOVED** [BOOL]
1. **DATAPACKED** [BOOL NULLABLE]
1. **OBJDATA** [BYTE(0) NULLABLE]
1. <span style='color: green'><b>DATAHASH</<b>b> [BYTE(20) NULLABLE]</span>

## VERSIONS
1. **VERNUM** [Numeric(10)]
1. **USERID** [GUID]
1. **VERDATE** [DateTime]
1. <span style='color: green'><b>PVERSION</b> [BYTE(8)]</span>
1. <span style='color: green'><b>CVERSION</b> [BYTE(4)]</span>
1. **CODE** [String(256) NULLABLE]
1. **COMMENT** [String(0) NULLABLE]
1. **SNAPSHOTMAKER** [GUID NULLABLE]
1. **SNAPSHOTCRC** [BYTE(4) NULLABLE]
1. <span style='color: green'><b>VERSIONID</b> [GUID]</span>

## EXTERNALS
1. **OBJID** [GUID]
1. **VERNUM** [Numeric(10)]
1. **EXTNAME** [String(128)]
1. **EXTVERID** [GUID]
1. **DATAPACKED** [BOOL]
1. **EXTDATA** [BYTE(0)]
1. <span style='color: green'><b>DATAHASH</b> [BYTE(20) NULLABLE]</span>