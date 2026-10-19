create table public.user_settings (
    id          uuid primary key default gen_random_uuid(),
    profile_id  uuid not null references public.profiles(id) on delete cascade,
    theme       text not null default 'system' check (theme in ('light', 'dark', 'system')),
    notifications_enabled boolean not null default true,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index idx_user_settings_profile_id on public.user_settings (profile_id);

alter table public.user_settings enable row level security;

create policy "Users can view own settings"
    on public.user_settings
    for select
    using (true);

create trigger trg_user_settings_updated
    before update on public.user_settings
    for each row execute function public.set_updated_at();
