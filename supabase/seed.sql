-- Sample seed data for local development & disaster recovery verification
-- This file is automatically executed when running `supabase start` or `supabase db reset`.

insert into public.profiles (id, username, full_name, avatar_url, website)
values 
    ('00000000-0000-0000-0000-000000000001', 'johndoe', 'John Doe', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e', 'https://example.com'),
    ('00000000-0000-0000-0000-000000000002', 'janedoe', 'Jane Doe', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330', 'https://example.com/jane'),
    ('00000000-0000-0000-0000-000000000003', 'alice', 'Alice Developer', 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80', 'https://alice.dev')
on conflict (username) do update set full_name = excluded.full_name;

insert into public.user_settings (id, profile_id, theme, notifications_enabled)
values
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'dark', true),
    ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002', 'light', false),
    ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000003', 'system', true)
on conflict (id) do nothing;

