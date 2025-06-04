import re
from services.configuration.logger import get_logger

logger = get_logger("ForbiddenKeywordsLogger")

forbidden_keywords = {
    "optimize table", "optimize index", "optimize query", "restructure table", "reformat table",
    "resize table", "extend table", "compress table", "defragment table", "merge rows", "split rows", 
    "update schema", "modify schema", "change schema", "add schema", "drop schema", "merge schema", 
    "drop row if exists", "modify row if exists", "clear table", "reset table schema", "adjust table", 
    "refresh index", "rebuild schema", "compress index", "resize schema", "extend column", "adjust column", 
    "refactor column", "remove index", "alter column constraints", "modify primary key", "rename schema", 
    "migrate column", "convert column type", "set column format", "alter column permissions", "check column value", 
    "insert value", "update value", "reorganize column", "restore column values", "revalidate column", "revert column", 
    "set column properties", "add column constraint", "remove column constraint", "restructure schema", 
    "refresh column", "renormalize table", "validate table", "reset table structure", "rebuild foreign key", 
    "reset index", "modify table permissions", "reset index type", "reorganize rows", "alter data structure", 
    "expand rows", "reduce rows", "purge table", "purge rows", "reindex table", "restructure partition", 
    "resize rows", "reset row permissions", "revise table schema", "apply index", "rebuild table partition", 
    "revert column format", "restore table values", "synchronize index", "restore row", "reset foreign key", 
    "configure index", "compact table", "adjust table partition", "compress rows", "adjust partition", 
    "set row structure", "truncate partition", "merge rows", "modify index properties", "apply foreign key", 
    "drop schema if exists", "insert row if not exists", "alter data", "modularize table", "optimize table schema", 
    "remove partition", "modify partition key", "alter column properties", "validate partition", "insert table schema", 
    "expand schema", "reduce partition", "increase row length", "remove table partition", "add table partition", 
    "insert values into schema", "restructure data", "expand foreign key", "validate partition key", "optimize schema", 
    "insert column", "increase index size", "decrease index size", "modify column data type", "change column data type", 
    "decrease column length", "insert schema data", "optimize column structure", "remove schema constraint", 
    "update schema permissions", "resize index", "optimize row data", "check row integrity", "resize foreign key", 
    "create foreign key constraint", "remove foreign key constraint", "merge foreign key", "alter partition permissions", 
    "reset foreign key constraints", "add schema permissions", "drop schema permissions", "truncate rows", 
    "adjust index length", "modify index order", "resize schema partition", "insert column constraint", 
    "merge partition", "add partition constraint", "remove index constraint", "alter row properties", 
    "reset column structure", "expand column", "reduce table data", "truncate column data", "increase table row", 
    "decrease row length", "resize column", "expand foreign key", "decrease column index", "set table primary key", 
    "truncate foreign key", "set index constraint", "modify primary key constraint", "restructure rows data", 
    "modify index values", "set row constraint", "update table structure", "check column constraint", 
    "modify index data", "expand table schema", "validate table constraints", "delete foreign key", "update index type",
    # SQL operation 
    "alter", "change", "modify", "update", "rename", "delete", "insert", "add", "drop", 
    "rebuild", "restructure", "reorganize", "reformat", "redefine", "shift", "transpose", 
    "transform", "override", "replace", "substitute", "exchange", "swap", "relocate", "move", 
    "resize", "extend", "contract", "shorten", "lengthen", "widen", "narrow", "expand", 
    "inflate", "deflate", "initialize", "create", "build", "assemble", "construct", "form", 
    "compose", "design", "construct", "create table", "create index", "add index", "drop index", 
    "rename index", "alter table", "alter column", "alter index", "drop column", "modify column", 
    "add column", "remove column", "rename column", "set column", "add primary key", "drop primary key", 
    "alter primary key", "add foreign key", "drop foreign key", "alter foreign key", "add constraint", 
    "drop constraint", "modify constraint", "rename constraint", "add unique constraint", 
    "drop unique constraint", "add check constraint", "drop check constraint", "alter check constraint", 
    "set column default", "remove column default", "change column type", "alter column type", 
    "increase column size", "decrease column size", "modify column size", "set column nullable", 
    "set column not nullable", "alter column name", "add foreign key constraint", "drop foreign key constraint", 
    "add check constraint", "drop check constraint", "add unique constraint", "drop unique constraint", 
    "rename table", "modify table name", "alter table permissions", "set table permissions", 
    "grant permissions", "revoke permissions", "check permissions", "set column permission", 
    "set table permission", "update table permissions", "remove table permissions", "alter schema", 
    "add foreign key", "drop foreign key", "modify foreign key", "add trigger", "drop trigger", 
    "modify trigger", "rename trigger", "add stored procedure", "drop stored procedure", "modify stored procedure", 
    "rename stored procedure", "add function", "drop function", "modify function", "rename function", 
    "update indexes", "drop indexes", "set index type", "change index order", "set index uniqueness", 
    "add composite primary key", "drop composite primary key", "alter composite primary key", 
    "reset auto increment", "set column to auto increment", "set column to unique", "set column as primary key", 
    "modify auto increment", "change column auto increment", "add sequence", "drop sequence", "alter sequence", 
    "update sequence", "change sequence", "modify sequence", "reset sequence", "add auto increment", 
    "set table to read-only", "set table to read-write", "enable table trigger", "disable table trigger", 
    "check table integrity", "check column integrity", "set table partition", "drop table partition", 
    "alter table partition", "set column partition", "drop column partition", "change partition key", 
    "add partition", "drop partition", "merge partition", "alter partition", "split partition", 
    "check column type", "check column size", "update column length", "alter table constraint", 
    "alter column constraints", "update table schema", "change table schema", "remove table schema", 
    "modify table structure", "alter table permissions", "set table structure", "modify column constraint", 
    "remove rows", "delete rows", "truncate table", "insert rows", "insert values", "update rows", 
    "update table", "insert into table", "select into table", "drop rows", "drop values", "set column value", 
    "delete column value", "rename column value", "assign value", "update value", "set default value", 
    "change default value", "update column default", "drop default value", "reset column default", 
    "alter default constraint", "add default constraint", "remove default constraint", "increase table size", 
    "decrease table size", "expand table", "reduce table", "optimize table", "optimize query", "optimize index", 
    "reorganize index", "rebuild index", "restructure table", "reformat table", "reset table", "reload table", 
    "refresh table", "recreate table", "restore table", "synchronize table", "reset column", "modify index type", 
    "update column size", "increase column size", "decrease column size", "update column type", "alter row", 
    "drop row", "delete row", "set row", "update row", "insert row", "rebuild table", "restore schema", 
    "revert table", "restore column", "reorganize schema", "update schema", "alter partition key", 
    "restore partition", "change row format", "set row format", "optimize row", "increase row size", 
    "decrease row size", "set column auto", "modify partition", "update partition", "drop partition", 
    "move partition", "resize partition", "increase partition", "reorganize partition", "truncate column", 
    "truncate index", "truncate table"
}

forbidden_patterns = [re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE) for keyword in forbidden_keywords]

def Contains_Forbidden_Keywords(query: str) -> bool:
    query = query.strip()
    logger.debug(f"Checking query for forbidden keywords: {query}")
    for pattern in forbidden_patterns:
        if pattern.search(query):
            logger.warning(f"Forbidden keyword detected in query: {query}")
            return True
    return False
