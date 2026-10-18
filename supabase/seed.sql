-- Sample seed data for local development
-- This file is automatically executed when running `supabase start` or `supabase db reset`.

insert into public.profiles (username, full_name, avatar_url, website)
values 
    ('johndoe', 'John Doe', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e', 'https://example.com'),
    ('janedoe', 'Jane Doe', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330', 'https://example.com/jane'),
    ('alice', 'Alice Developer', 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80', 'https://alice.dev')
on conflict (username) do nothing;
