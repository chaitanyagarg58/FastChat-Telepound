--
-- PostgreSQL database dump
--

-- Dumped from database version 12.12 (Ubuntu 12.12-0ubuntu0.20.04.1)
-- Dumped by pg_dump version 12.12 (Ubuntu 12.12-0ubuntu0.20.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: clientinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clientinfo (
    username text NOT NULL,
    password text,
    public_n text,
    public_e text,
    private_d text,
    private_p text,
    private_q text,
    salt text
);


ALTER TABLE public.clientinfo OWNER TO postgres;

--
-- Name: groupinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.groupinfo (
    groupname text,
    admin text,
    members text[]
);


ALTER TABLE public.groupinfo OWNER TO postgres;

--
-- Name: undelivered; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.undelivered (
    "time" double precision NOT NULL,
    touser text NOT NULL,
    message text NOT NULL
);


ALTER TABLE public.undelivered OWNER TO postgres;

--
-- Name: clientinfo clientinfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientinfo
    ADD CONSTRAINT clientinfo_pkey PRIMARY KEY (username);


--
-- Name: undelivered undelivered_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.undelivered
    ADD CONSTRAINT undelivered_pkey PRIMARY KEY ("time");


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

GRANT SELECT ON SCHEMA public TO client;


--
-- Name: TABLE clientinfo; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT ON TABLE public.clientinfo TO client;

--
-- Name: TABLE groupinfo; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT ON TABLE public.groupinfo TO client;

--
-- PostgreSQL database dump complete
--
