--
-- PostgreSQL database dump
--
-- FICTIONAL SAMPLE DATA. A deliberately well-designed schema used to check for false positives.
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

CREATE TABLE public.schema_migrations (
    version character varying(40) NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT pk_schema_migrations PRIMARY KEY (version)
);
COMMENT ON TABLE public.schema_migrations IS 'Applied schema changes. Owner: platform.';

CREATE TABLE public.currencies (
    currency_code character(3) NOT NULL,
    name character varying(60) NOT NULL,
    minor_units smallint NOT NULL,
    CONSTRAINT pk_currencies PRIMARY KEY (currency_code),
    CONSTRAINT check_currencies_minor_units CHECK (minor_units BETWEEN 0 AND 4)
);
COMMENT ON TABLE public.currencies IS 'ISO 4217 currencies used by the shop.';
COMMENT ON COLUMN public.currencies.currency_code IS 'ISO 4217 alphabetic code.';
COMMENT ON COLUMN public.currencies.name IS 'English currency name.';
COMMENT ON COLUMN public.currencies.minor_units IS 'Digits after the decimal point.';

CREATE TABLE public.customers (
    customer_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    email character varying(254) NOT NULL,
    display_name character varying(120) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(60) NOT NULL,
    updated_by character varying(60) NOT NULL,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id),
    CONSTRAINT unique_customers_email UNIQUE (email)
);
COMMENT ON TABLE public.customers IS 'People who buy from the shop. Owner: sales. Classification: confidential.';

CREATE TABLE public.products (
    product_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    sku character varying(40) NOT NULL,
    name character varying(160) NOT NULL,
    unit_price numeric(14,4) NOT NULL,
    currency_code character(3) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(60) NOT NULL,
    updated_by character varying(60) NOT NULL,
    CONSTRAINT pk_products PRIMARY KEY (product_id),
    CONSTRAINT unique_products_sku UNIQUE (sku),
    CONSTRAINT check_products_price CHECK (unit_price >= 0),
    CONSTRAINT fk_products_currency FOREIGN KEY (currency_code) REFERENCES public.currencies (currency_code) ON UPDATE RESTRICT ON DELETE RESTRICT
);
CREATE INDEX index_products_currency_code ON public.products USING btree (currency_code);
COMMENT ON TABLE public.products IS 'Items for sale. Owner: catalog.';

CREATE TABLE public.orders (
    order_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    customer_id bigint NOT NULL,
    status character varying(20) NOT NULL,
    total_amount numeric(14,4) NOT NULL,
    currency_code character(3) NOT NULL,
    ordered_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(60) NOT NULL,
    updated_by character varying(60) NOT NULL,
    CONSTRAINT pk_orders PRIMARY KEY (order_id),
    CONSTRAINT check_orders_status CHECK (status IN ('open', 'shipped', 'cancelled')),
    CONSTRAINT check_orders_total CHECK (total_amount >= 0),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES public.customers (customer_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_orders_currency FOREIGN KEY (currency_code) REFERENCES public.currencies (currency_code) ON UPDATE RESTRICT ON DELETE RESTRICT
);
CREATE INDEX index_orders_customer_id ON public.orders USING btree (customer_id);
CREATE INDEX index_orders_currency_code ON public.orders USING btree (currency_code);
COMMENT ON TABLE public.orders IS 'Customer orders. Owner: sales.';

CREATE TABLE public.order_items (
    order_item_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    order_id bigint NOT NULL,
    product_id bigint NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(14,4) NOT NULL,
    currency_code character(3) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(60) NOT NULL,
    updated_by character varying(60) NOT NULL,
    CONSTRAINT pk_order_items PRIMARY KEY (order_item_id),
    CONSTRAINT unique_order_items_line UNIQUE (order_id, product_id),
    CONSTRAINT check_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT check_order_items_price CHECK (unit_price >= 0),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES public.orders (order_id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES public.products (product_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_order_items_currency FOREIGN KEY (currency_code) REFERENCES public.currencies (currency_code) ON UPDATE RESTRICT ON DELETE RESTRICT
);
CREATE INDEX index_order_items_product_id ON public.order_items USING btree (product_id);
CREATE INDEX index_order_items_currency_code ON public.order_items USING btree (currency_code);
COMMENT ON TABLE public.order_items IS 'Lines of an order. Owner: sales.';

CREATE TABLE public.audit_log (
    audit_log_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    table_name character varying(63) NOT NULL,
    record_key character varying(100) NOT NULL,
    action character varying(10) NOT NULL,
    changed_at timestamp with time zone DEFAULT now() NOT NULL,
    changed_by character varying(60) NOT NULL,
    CONSTRAINT pk_audit_log PRIMARY KEY (audit_log_id),
    CONSTRAINT check_audit_log_action CHECK (action IN ('insert', 'update', 'delete'))
);
COMMENT ON TABLE public.audit_log IS 'Append-only record of data changes. Owner: platform.';

INSERT INTO public.schema_migrations (version) VALUES ('2025010101');

INSERT INTO public.currencies (currency_code, name, minor_units) VALUES ('EUR', 'Euro', 2), ('USD', 'US dollar', 2), ('PKR', 'Pakistani rupee', 2);

INSERT INTO public.customers (email, display_name, created_by, updated_by) VALUES
 ('alice@example.com', 'Alice Fictional', 'seed', 'seed'),
 ('bob@example.org', 'Bob Invented', 'seed', 'seed'),
 ('carol@example.net', 'Carol Madeup', 'seed', 'seed');

INSERT INTO public.products (sku, name, unit_price, currency_code, created_by, updated_by) VALUES
 ('MUG-001', 'Ceramic mug', 8.50, 'EUR', 'seed', 'seed'),
 ('TEA-010', 'Green tea', 4.20, 'EUR', 'seed', 'seed'),
 ('PEN-100', 'Fountain pen', 26.00, 'USD', 'seed', 'seed');

INSERT INTO public.orders (customer_id, status, total_amount, currency_code, ordered_at, created_by, updated_by) VALUES
 (1, 'shipped', 12.70, 'EUR', '2025-01-10 10:00:00+00', 'seed', 'seed'),
 (2, 'open', 26.00, 'USD', '2025-01-11 10:00:00+00', 'seed', 'seed');

INSERT INTO public.order_items (order_id, product_id, quantity, unit_price, currency_code, created_by, updated_by) VALUES
 (1, 1, 1, 8.50, 'EUR', 'seed', 'seed'),
 (1, 2, 1, 4.20, 'EUR', 'seed', 'seed'),
 (2, 3, 1, 26.00, 'USD', 'seed', 'seed');

--
-- PostgreSQL database dump complete
--
