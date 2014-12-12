Database
========
The aim of this file is to document the publically accessible Infobot databse of Subluminal.

Infobot uses a PostgreSQL database which is hosted on svkampen's server. Its schema is also published in this repo's `schema.sql` file but for easier usage and connecting we provide this document.

Connecting
----------
For whichever reason you wish to use the database you need a PostgreSQL tool or a suitable library in your programming language. The publically readable access details are the following:

* Host: `tehsvk.net`
* Port: `5432` (default)
* Username: `readonly`
* Password: `readonly`
* Database: `infobot`

Some PostgreSQL libraries also take a connection string: `postgres://readonly:readonly@tehsvk.net/infobot`.

Usage
-----

#### Get info of a single user
`SELECT * FROM info('nick');`

#### Get info of multiple users
`SELECT * FROM multiinfo(ARRAY['nick', 'nick2', 'simmo']);` <br>
*NB! When using this function, make sure you pass the array into SQL correctly using your programming language's library.*

#### Get nick's info history
`SELECT * FROM infohistory('nick');`

Tables
------
Infobot runs on two tables: infos and aliases:

### infos
This table stores all the infos ever set. When someone changes their info it's added as a new row with a new timestamp to keep a complete history of all infos.

**Columns**:

* `id` - unique info identifier
* `nick` - setter's nickname
* `user` - setter's username <br>
  *NB! When using this column in a SQL query it must be written as `"user"` since it happens to also be a PostgreSQL keyword*
* `host` - setter's hostname
* `info` - actual info text itself
* `ts` - timestamp telling when the info was added, in UTC, `-infinity` means this row was imported from old infobot

### aliases
This table contains the current alias mappings. <br>
*NB! Since Infobot supports multiple levels of aliases, i.e. setting your alias to another nick which also has an alias set, the rows in this table only contain only the next nickname and not the final nickname whose info will be shown. To get around this refer to Functions section below*

**Columns**:

* `nick` - setter's nickname
* `alias` - nickname whose info the current nickname will point to
* `ts` - timestamp when the alias was set, in UTC, `-infinity` means this row was imported from old infobot

Functions
---------
Only functions available to the read-only user are documented here as they're the only ones this user can execute.

### alias
`FUNCTION alias(nick_ character varying) RETURNS character varying`

Iterates the entire multi-level alias chain of `nick_` and returns the final nickname whose info it will have.

### aliaschain
`FUNCTION aliaschain(nick_ character varying) RETURNS TABLE(i integer, nick character varying)`

Iterates the entire multi-level alias chain of `nick_` and returns the entire chain with all intermediate nicknames.

### info
`FUNCTION info(nick_ character varying) RETURNS SETOF infos`

Returns the full infos table row corresponding to `nick_`'s current info. When no info was found no rows are returned.

### multiinfo
	FUNCTION multiinfo(nicks_ character varying[]) 
    RETURNS TABLE(alias character varying, id integer, nick character varying, "user" character varying, host character varying, info text, ts timestamp without time zone)

Returns the full infos table rows for corresponding nicknames in the array `nicks_`. The returned rows have an additional first column `alias` which indicates the nickname from input array for which the following info is. This is necessary to allow matching returned infos to their respective input nicknames. When no info was found for some nickname all columns except `alias` will be `NULL`s in that row.

### infoid
`FUNCTION infoid(nick_ character varying) RETURNS integer`

Returns just the info's `id` of the given `nick_` after iterating the alias chain.

### infoid2
`FUNCTION infoid2(nick_ character varying) RETURNS integer`

Returns just the info's `id` of the given `nick_` **without** iterating the alias chain.

### infohistory
`FUNCTION infohistory(nick_ character varying) RETURNS SETOF infos`

Returns the full infos table rows corresponding to `nick_`'s all historical infos.
