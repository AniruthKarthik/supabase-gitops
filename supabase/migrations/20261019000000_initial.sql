-- Migration: Initial Starter Schema
-- This is a sample starter schema for the Supabase GitOps template.
-- You can modify or replace this file with your own application tables.

create table public.profiles (
    id          uuid primary key default gen_random_uuid(),
    username    text unique check (length(username) >= 3),
    full_name   text,
    avatar_url  text,
    website     text,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index idx_profiles_username on public.profiles (username);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger trg_profiles_updated
    before update on public.profiles
    for each row execute function public.set_updated_at();

alter table public.profiles enable row level security;

create policy "public profiles are viewable by everyone"
    on public.profiles
    for select
    using (true);
