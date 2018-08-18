--
-- PostgreSQL database dump
--

-- Dumped from database version 10.5 (Ubuntu 10.5-0ubuntu0.18.04)
-- Dumped by pg_dump version 10.5 (Ubuntu 10.5-0ubuntu0.18.04)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: addalias(character varying, character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.addalias(nick_ character varying, alias_ character varying) RETURNS boolean
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

CREATE FUNCTION public.addinfo(nick_ character varying, user_ character varying, host_ character varying, info_ character varying) RETURNS integer
    LANGUAGE sql
    AS $$
SELECT delalias(nick_);
INSERT INTO infos VALUES (DEFAULT, nick_, user_, host_, info_) RETURNING id;
$$;


ALTER FUNCTION public.addinfo(nick_ character varying, user_ character varying, host_ character varying, info_ character varying) OWNER TO infobot;

--
-- Name: alias(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.alias(nick_ character varying) RETURNS character varying
    LANGUAGE sql STABLE
    AS $$
SELECT nick FROM aliaschain(nick_) ORDER BY i DESC LIMIT 1;
$$;


ALTER FUNCTION public.alias(nick_ character varying) OWNER TO infobot;

--
-- Name: aliaschain(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.aliaschain(nick_ character varying) RETURNS TABLE(i integer, nick character varying)
    LANGUAGE sql STABLE ROWS 2
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
-- Name: copyinfo(character varying, character varying, character varying, integer); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.copyinfo(nick_ character varying, user_ character varying, host_ character varying, id_ integer) RETURNS integer
    LANGUAGE sql
    AS $$
SELECT delalias(nick_);
INSERT INTO infos VALUES (DEFAULT, nick_, user_, host_, (SELECT info FROM infos WHERE id = id_)) RETURNING id;
$$;


ALTER FUNCTION public.copyinfo(nick_ character varying, user_ character varying, host_ character varying, id_ integer) OWNER TO infobot;

--
-- Name: delalias(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.delalias(nick_ character varying) RETURNS void
    LANGUAGE sql
    AS $$
DELETE FROM aliases WHERE lower(nick) = lower(nick_);
$$;


ALTER FUNCTION public.delalias(nick_ character varying) OWNER TO infobot;

--
-- Name: delinfo(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.delinfo(nick_ character varying) RETURNS void
    LANGUAGE sql
    AS $$
SELECT addalias(nick_, NULL);
SELECT null::void; -- Crate a bogus matching return value for SQL to stop whining
$$;


ALTER FUNCTION public.delinfo(nick_ character varying) OWNER TO infobot;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: infos; Type: TABLE; Schema: public; Owner: infobot
--

CREATE TABLE public.infos (
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

CREATE FUNCTION public.info(nick_ character varying) RETURNS SETOF public.infos
    LANGUAGE sql STABLE ROWS 1
    AS $$
SELECT * FROM infos WHERE id = (SELECT infoid(nick_));
$$;


ALTER FUNCTION public.info(nick_ character varying) OWNER TO infobot;

--
-- Name: infohistory(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.infohistory(nick_ character varying) RETURNS SETOF public.infos
    LANGUAGE sql ROWS 1
    AS $$
SELECT infos.* FROM infos, aliaschain(nick_) as ac WHERE infos.nick = ac.nick ORDER BY infos.id;
$$;


ALTER FUNCTION public.infohistory(nick_ character varying) OWNER TO infobot;

--
-- Name: infoid(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.infoid(nick_ character varying) RETURNS integer
    LANGUAGE sql STABLE
    AS $$
SELECT id FROM infos WHERE lower(nick) = lower(alias(nick_)) ORDER BY ts DESC LIMIT 1;
$$;


ALTER FUNCTION public.infoid(nick_ character varying) OWNER TO infobot;

--
-- Name: infoid2(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.infoid2(nick_ character varying) RETURNS integer
    LANGUAGE sql
    AS $$
SELECT id FROM infos WHERE lower(nick) = lower(nick_) ORDER BY ts DESC LIMIT 1;
$$;


ALTER FUNCTION public.infoid2(nick_ character varying) OWNER TO infobot;

--
-- Name: latesttimestamp(character varying); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.latesttimestamp(nick character varying) RETURNS timestamp without time zone
    LANGUAGE sql COST 10
    AS $_$
  SELECT ts FROM infos WHERE infos.nick = $1 ORDER BY ts DESC LIMIT 1; $_$;


ALTER FUNCTION public.latesttimestamp(nick character varying) OWNER TO infobot;

--
-- Name: multiinfo(character varying[]); Type: FUNCTION; Schema: public; Owner: infobot
--

CREATE FUNCTION public.multiinfo(nicks_ character varying[]) RETURNS TABLE(alias character varying, id integer, nick character varying, "user" character varying, host character varying, info text, ts timestamp without time zone)
    LANGUAGE sql ROWS 100
    AS $$
SELECT nicks, infos.* FROM unnest(nicks_) AS nicks
LEFT JOIN infos ON infos.id = (SELECT infoid(nicks));
$$;


ALTER FUNCTION public.multiinfo(nicks_ character varying[]) OWNER TO infobot;

--
-- Name: aliases; Type: TABLE; Schema: public; Owner: infobot
--

CREATE TABLE public.aliases (
    nick character varying(64) NOT NULL,
    alias character varying(64),
    ts timestamp without time zone DEFAULT timezone('utc'::text, now())
);


ALTER TABLE public.aliases OWNER TO infobot;

--
-- Name: aliasinfos; Type: VIEW; Schema: public; Owner: infobot
--

CREATE VIEW public.aliasinfos AS
 SELECT a.alias AS rootnick,
    a.ag AS nicks,
    infos.info
   FROM ( SELECT m.alias,
            array_agg(m.nick) AS ag
           FROM ( SELECT aliases.nick,
                    public.alias(aliases.nick) AS alias
                   FROM public.aliases
                UNION
                 SELECT DISTINCT infos_1.nick,
                    infos_1.nick
                   FROM public.infos infos_1
                  WHERE (NOT (EXISTS ( SELECT NULL::text AS unknown
                           FROM public.aliases
                          WHERE (lower((aliases.nick)::text) = lower((aliases.nick)::text)))))) m
          GROUP BY m.alias) a,
    public.infos
  WHERE (infos.id = ( SELECT public.infoid2(a.alias) AS infoid2));


ALTER TABLE public.aliasinfos OWNER TO infobot;

--
-- Name: bots; Type: TABLE; Schema: public; Owner: infobot
--

CREATE TABLE public.bots (
    id integer NOT NULL,
    cmdchar character varying(4) NOT NULL,
    bot character varying(64) NOT NULL,
    owner character varying(64)
);


ALTER TABLE public.bots OWNER TO infobot;

--
-- Name: bots_id_seq; Type: SEQUENCE; Schema: public; Owner: infobot
--

CREATE SEQUENCE public.bots_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bots_id_seq OWNER TO infobot;

--
-- Name: bots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infobot
--

ALTER SEQUENCE public.bots_id_seq OWNED BY public.bots.id;


--
-- Name: infos_id_seq; Type: SEQUENCE; Schema: public; Owner: infobot
--

CREATE SEQUENCE public.infos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.infos_id_seq OWNER TO infobot;

--
-- Name: infos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infobot
--

ALTER SEQUENCE public.infos_id_seq OWNED BY public.infos.id;


--
-- Name: latestinfos; Type: VIEW; Schema: public; Owner: infobot
--

CREATE VIEW public.latestinfos AS
 SELECT infos.id,
    infos.nick,
    infos."user",
    infos.host,
    infos.info,
    infos.ts
   FROM public.infos
  WHERE (infos.ts = ( SELECT public.latesttimestamp(infos.nick) AS latesttimestamp));


ALTER TABLE public.latestinfos OWNER TO infobot;

--
-- Name: reminders; Type: TABLE; Schema: public; Owner: infobot
--

CREATE TABLE public.reminders (
    id integer NOT NULL,
    from_nick character varying(64) NOT NULL,
    to_nick character varying(64) NOT NULL,
    message text NOT NULL,
    channel text NOT NULL,
    begints timestamp without time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    endts timestamp without time zone NOT NULL,
    fulfilled boolean DEFAULT false NOT NULL
);


ALTER TABLE public.reminders OWNER TO infobot;

--
-- Name: reminders_id_seq; Type: SEQUENCE; Schema: public; Owner: infobot
--

CREATE SEQUENCE public.reminders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reminders_id_seq OWNER TO infobot;

--
-- Name: reminders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infobot
--

ALTER SEQUENCE public.reminders_id_seq OWNED BY public.reminders.id;


--
-- Name: tells; Type: TABLE; Schema: public; Owner: infobot
--

CREATE TABLE public.tells (
    tellid integer NOT NULL,
    from_nick character varying(64) NOT NULL,
    to_nick character varying(64) NOT NULL,
    message text NOT NULL,
    begints timestamp without time zone DEFAULT timezone('utc'::text, now()),
    fulfilled boolean DEFAULT false
);


ALTER TABLE public.tells OWNER TO infobot;

--
-- Name: tells_tellid_seq; Type: SEQUENCE; Schema: public; Owner: infobot
--

CREATE SEQUENCE public.tells_tellid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tells_tellid_seq OWNER TO infobot;

--
-- Name: tells_tellid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infobot
--

ALTER SEQUENCE public.tells_tellid_seq OWNED BY public.tells.tellid;


--
-- Name: bots id; Type: DEFAULT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.bots ALTER COLUMN id SET DEFAULT nextval('public.bots_id_seq'::regclass);


--
-- Name: infos id; Type: DEFAULT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.infos ALTER COLUMN id SET DEFAULT nextval('public.infos_id_seq'::regclass);


--
-- Name: reminders id; Type: DEFAULT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.reminders ALTER COLUMN id SET DEFAULT nextval('public.reminders_id_seq'::regclass);


--
-- Name: tells tellid; Type: DEFAULT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.tells ALTER COLUMN tellid SET DEFAULT nextval('public.tells_tellid_seq'::regclass);


--
-- Name: aliases alias_pkey; Type: CONSTRAINT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.aliases
    ADD CONSTRAINT alias_pkey PRIMARY KEY (nick);


--
-- Name: bots bots_pkey; Type: CONSTRAINT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.bots
    ADD CONSTRAINT bots_pkey PRIMARY KEY (id);


--
-- Name: bots cmdchar_bot_uniq; Type: CONSTRAINT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.bots
    ADD CONSTRAINT cmdchar_bot_uniq UNIQUE (cmdchar, bot);


--
-- Name: infos infos_pkey; Type: CONSTRAINT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.infos
    ADD CONSTRAINT infos_pkey PRIMARY KEY (id);


--
-- Name: reminders reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.reminders
    ADD CONSTRAINT reminders_pkey PRIMARY KEY (id);


--
-- Name: tells tells_pkey; Type: CONSTRAINT; Schema: public; Owner: infobot
--

ALTER TABLE ONLY public.tells
    ADD CONSTRAINT tells_pkey PRIMARY KEY (tellid);


--
-- Name: info_nick_index; Type: INDEX; Schema: public; Owner: infobot
--

CREATE INDEX info_nick_index ON public.infos USING btree (nick);


--
-- Name: infos_lower_nick_ts_desc_index; Type: INDEX; Schema: public; Owner: infobot
--

CREATE INDEX infos_lower_nick_ts_desc_index ON public.infos USING btree (lower(nick), ts DESC);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA public TO readonly;


--
-- Name: TABLE infos; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON TABLE public.infos TO readonly;


--
-- Name: TABLE aliases; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON TABLE public.aliases TO readonly;


--
-- Name: TABLE aliasinfos; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON TABLE public.aliasinfos TO readonly;


--
-- Name: TABLE bots; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON TABLE public.bots TO readonly;


--
-- Name: SEQUENCE bots_id_seq; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON SEQUENCE public.bots_id_seq TO readonly;


--
-- Name: SEQUENCE infos_id_seq; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON SEQUENCE public.infos_id_seq TO readonly;


--
-- Name: TABLE latestinfos; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON TABLE public.latestinfos TO readonly;


--
-- Name: TABLE reminders; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON TABLE public.reminders TO readonly;


--
-- Name: SEQUENCE reminders_id_seq; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON SEQUENCE public.reminders_id_seq TO readonly;


--
-- Name: TABLE tells; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON TABLE public.tells TO readonly;


--
-- Name: SEQUENCE tells_tellid_seq; Type: ACL; Schema: public; Owner: infobot
--

GRANT SELECT ON SEQUENCE public.tells_tellid_seq TO readonly;


--
-- PostgreSQL database dump complete
--

