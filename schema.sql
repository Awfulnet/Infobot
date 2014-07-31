--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Name: addalias(character varying, character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION addalias(nick_ character varying, alias_ character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
  cyclic boolean;

BEGIN
SELECT (SELECT nick FROM aliaschain(alias_) WHERE lower(nick) = lower(nick_)) IS NULL INTO cyclic;

IF cyclic THEN
  PERFORM delalias(nick_);
  INSERT INTO aliases VALUES (nick_, alias_);
END IF;

RETURN cyclic;
END;
$$;


ALTER FUNCTION public.addalias(nick_ character varying, alias_ character varying) OWNER TO infobot;

--
-- Name: addinfo(character varying, character varying, character varying, character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION addinfo(nick_ character varying, user_ character varying, host_ character varying, info_ character varying) RETURNS integer
    LANGUAGE sql
    AS $$
SELECT delalias(nick_);
INSERT INTO infos VALUES (DEFAULT, nick_, user_, host_, info_) RETURNING id;
$$;


ALTER FUNCTION public.addinfo(nick_ character varying, user_ character varying, host_ character varying, info_ character varying) OWNER TO infobot;

--
-- Name: alias(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION alias(nick_ character varying) RETURNS character varying
    LANGUAGE sql
    AS $$
SELECT nick FROM aliaschain(nick_) ORDER BY i DESC LIMIT 1;
$$;


ALTER FUNCTION public.alias(nick_ character varying) OWNER TO infobot;

--
-- Name: aliaschain(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION aliaschain(nick_ character varying) RETURNS TABLE(i integer, nick character varying)
    LANGUAGE sql ROWS 2
    AS $$
WITH RECURSIVE chain(i, nick) AS (
    VALUES (0, nick_)
  UNION
    SELECT chain.i + 1, aliases.alias FROM aliases, chain WHERE lower(aliases.nick) = lower(chain.nick)
)
SELECT * FROM chain;
$$;


ALTER FUNCTION public.aliaschain(nick_ character varying) OWNER TO infobot;

--
-- Name: delalias(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION delalias(nick_ character varying) RETURNS void
    LANGUAGE sql
    AS $$
DELETE FROM aliases WHERE lower(nick) = lower(nick_);
$$;


ALTER FUNCTION public.delalias(nick_ character varying) OWNER TO infobot;

--
-- Name: delinfo(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION delinfo(nick_ character varying) RETURNS void
    LANGUAGE sql
    AS $$
SELECT addalias(nick_, NULL);
SELECT null::void; -- Crate a bogus matching return value for SQL to stop whining
$$;


ALTER FUNCTION public.delinfo(nick_ character varying) OWNER TO infobot;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: infos; Type: TABLE; Schema: public; Owner: infobot; Tablespace: 
--

CREATE TABLE infos (
    id integer NOT NULL,
    nick character varying(64) NOT NULL,
    "user" character varying(64),
    host character varying(64),
    info text,
    ts timestamp without time zone DEFAULT timezone('utc'::text, now())
);


ALTER TABLE public.infos OWNER TO infobot;

--
-- Name: info(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION info(nick_ character varying) RETURNS SETOF infos
    LANGUAGE sql ROWS 1
    AS $$
SELECT * FROM infos WHERE id = (SELECT infoid(nick_));
$$;


ALTER FUNCTION public.info(nick_ character varying) OWNER TO infobot;

--
-- Name: infoid(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION infoid(nick_ character varying) RETURNS integer
    LANGUAGE sql
    AS $$
SELECT id FROM infos WHERE lower(nick) = lower(alias(nick_)) ORDER BY ts DESC LIMIT 1;
$$;


ALTER FUNCTION public.infoid(nick_ character varying) OWNER TO infobot;

--
-- Name: infoid2(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION infoid2(nick_ character varying) RETURNS integer
    LANGUAGE sql
    AS $$
SELECT id FROM infos WHERE lower(nick) = lower(nick_) ORDER BY ts DESC LIMIT 1;
$$;


ALTER FUNCTION public.infoid2(nick_ character varying) OWNER TO infobot;

--
-- Name: multiinfo(character varying[]); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION multiinfo(nicks_ character varying[]) RETURNS TABLE(alias character varying, id integer, nick character varying, "user" character varying, host character varying, info text, ts timestamp without time zone)
    LANGUAGE sql ROWS 100
    AS $$
SELECT nicks, infos.* FROM unnest(nicks_) AS nicks
LEFT JOIN infos ON infos.id = (SELECT infoid(nicks));
$$;


ALTER FUNCTION public.multiinfo(nicks_ character varying[]) OWNER TO infobot;

--
-- Name: aliases; Type: TABLE; Schema: public; Owner: infobot; Tablespace: 
--

CREATE TABLE aliases (
    nick character varying(64) NOT NULL,
    alias character varying(64),
    ts timestamp without time zone DEFAULT timezone('utc'::text, now())
);


ALTER TABLE public.aliases OWNER TO infobot;

--
-- Name: aliasinfos; Type: VIEW; Schema: public; Owner: infobot
--

CREATE VIEW aliasinfos AS
 SELECT a.alias AS rootnick,
    a.ag AS nicks,
    infos.info
   FROM ( SELECT m.alias,
            array_agg(m.nick) AS ag
           FROM ( SELECT aliases.nick,
                    alias(aliases.nick) AS alias
                   FROM aliases
                UNION
                 SELECT DISTINCT infos_1.nick,
                    infos_1.nick
                   FROM infos infos_1
                  WHERE (NOT (EXISTS ( SELECT NULL::unknown
                           FROM aliases
                          WHERE (lower((aliases.nick)::text) = lower((aliases.nick)::text)))))) m
          GROUP BY m.alias) a,
    infos
  WHERE (infos.id = ( SELECT infoid2(a.alias) AS infoid2));


ALTER TABLE public.aliasinfos OWNER TO infobot;

--
-- Name: infos_id_seq; Type: SEQUENCE; Schema: public; Owner: infobot
--

CREATE SEQUENCE infos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.infos_id_seq OWNER TO infobot;

--
-- Name: infos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infobot
--

ALTER SEQUENCE infos_id_seq OWNED BY infos.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY infos ALTER COLUMN id SET DEFAULT nextval('infos_id_seq'::regclass);


--
-- Name: alias_pkey; Type: CONSTRAINT; Schema: public; Owner: infobot; Tablespace: 
--

ALTER TABLE ONLY aliases
    ADD CONSTRAINT alias_pkey PRIMARY KEY (nick);


--
-- Name: infos_pkey; Type: CONSTRAINT; Schema: public; Owner: infobot; Tablespace: 
--

ALTER TABLE ONLY infos
    ADD CONSTRAINT infos_pkey PRIMARY KEY (id);


--
-- Name: public; Type: ACL; Schema: -; Owner: svkampen
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM svkampen;
GRANT ALL ON SCHEMA public TO svkampen;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

