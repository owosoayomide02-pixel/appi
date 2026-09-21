-- OAuth identity columns for account sign-in
alter table public.users add column if not exists oauth_provider varchar(32);
alter table public.users add column if not exists oauth_subject varchar(160);
create index if not exists ix_users_oauth_provider on public.users (oauth_provider);
create index if not exists ix_users_oauth_subject on public.users (oauth_subject);
