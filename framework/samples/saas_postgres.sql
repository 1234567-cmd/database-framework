--
-- PostgreSQL database dump
--
-- FICTIONAL SAMPLE DATA. All tenants, people and emails are invented.
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: tenants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tenants (
    id bigint NOT NULL,
    name character varying(120) NOT NULL,
    plan character varying(20) NOT NULL,
    created_at timestamp without time zone NOT NULL
);

CREATE TABLE public.users (
    id bigint NOT NULL,
    tenant_id bigint,
    email character varying(160) NOT NULL,
    display_name character varying(120),
    created_at timestamp without time zone NOT NULL
);

CREATE TABLE public.projects (
    id bigint NOT NULL,
    tenant_id bigint NOT NULL,
    owner_id bigint NOT NULL,
    name character varying(160) NOT NULL,
    budget real,
    created_at timestamp without time zone NOT NULL
);

CREATE TABLE public.tasks (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    title character varying(200) NOT NULL,
    assignee_id bigint,
    status character varying(20) NOT NULL,
    created_at timestamp without time zone NOT NULL
);

CREATE TABLE public.comments (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    author_id bigint NOT NULL,
    body text NOT NULL,
    created_at timestamp without time zone NOT NULL
);

CREATE TABLE public.invoices (
    id bigint NOT NULL,
    tenant_id bigint NOT NULL,
    invoice_number character varying(30) NOT NULL,
    total double precision NOT NULL,
    issued_at timestamp without time zone NOT NULL
);

--
-- Data for Name: tenants; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tenants (id, name, plan, created_at) FROM stdin;
1	Northwind Example Inc	pro	2024-01-02 09:00:00
2	Fabrikam Sample Ltd	free	2024-02-03 09:00:00
3	Contoso Demo LLC	pro	2024-03-04 09:00:00
\.

COPY public.users (id, tenant_id, email, display_name, created_at) FROM stdin;
1	1	alice@example.com	Alice Fictional	2024-01-03 09:00:00
2	1	bob@example.com	Bob Invented	2024-01-04 09:00:00
3	2	carol@example.org	Carol Madeup	2024-02-04 09:00:00
4	2	dan@example.org	Dan Pretend	2024-02-05 09:00:00
5	3	erin@example.net	Erin Sample	2024-03-05 09:00:00
6	\N	frank@example.net	Frank Orphan	2024-03-06 09:00:00
\.

COPY public.projects (id, tenant_id, owner_id, name, budget, created_at) FROM stdin;
1	1	1	Website redesign	12000.5	2024-01-10 09:00:00
2	1	2	Mobile app	45000	2024-01-11 09:00:00
3	2	3	Warehouse move	9000.75	2024-02-10 09:00:00
4	3	3	Cross tenant project	100	2024-03-10 09:00:00
\.

COPY public.tasks (id, project_id, title, assignee_id, status, created_at) FROM stdin;
1	1	Draft wireframes	1	done	2024-01-12 09:00:00
2	1	Pick colors	2	open	2024-01-13 09:00:00
3	2	Set up CI	2	open	2024-01-14 09:00:00
4	3	Count stock	3	open	2024-02-11 09:00:00
5	4	Shared by mistake	1	open	2024-03-11 09:00:00
\.

COPY public.comments (id, task_id, author_id, body, created_at) FROM stdin;
1	1	1	Looks good	2024-01-15 09:00:00
2	4	3	Started counting	2024-02-12 09:00:00
3	5	5	Why can I see this?	2024-03-12 09:00:00
\.

COPY public.invoices (id, tenant_id, invoice_number, total, issued_at) FROM stdin;
1	1	INV-1001	99.9	2024-02-01 09:00:00
2	1	INV-1002	99.9	2024-03-01 09:00:00
3	2	INV-1003	0	2024-03-01 09:00:00
4	3	INV-1004	249.5	2024-04-01 09:00:00
\.

--
-- Constraints
--

ALTER TABLE ONLY public.tenants ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.users ADD CONSTRAINT users_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.projects ADD CONSTRAINT projects_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.tasks ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.comments ADD CONSTRAINT comments_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.invoices ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.users ADD CONSTRAINT users_email_key UNIQUE (email);

ALTER TABLE ONLY public.users ADD CONSTRAINT users_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);
ALTER TABLE ONLY public.projects ADD CONSTRAINT projects_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);
ALTER TABLE ONLY public.projects ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);
ALTER TABLE ONLY public.tasks ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);
ALTER TABLE ONLY public.tasks ADD CONSTRAINT tasks_assignee_id_fkey FOREIGN KEY (assignee_id) REFERENCES public.users(id);
ALTER TABLE ONLY public.comments ADD CONSTRAINT comments_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);
ALTER TABLE ONLY public.comments ADD CONSTRAINT comments_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);
ALTER TABLE ONLY public.invoices ADD CONSTRAINT invoices_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);

--
-- Privileges
--

CREATE ROLE app_user LOGIN;

GRANT ALL ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL ON SCHEMA public TO PUBLIC;

--
-- PostgreSQL database dump complete
--
