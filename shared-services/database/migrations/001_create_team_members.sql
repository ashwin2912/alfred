-- Migration: Create team_members table
-- Description: Centralized team member storage for Discord bot and ClickUp integration
-- Date: 2024-12-09

-- Create team_members table
CREATE TABLE IF NOT EXISTS public.team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,

    -- Integration identifiers
    discord_username TEXT UNIQUE,
    clickup_user_id TEXT,
    clickup_api_token TEXT, -- Optional: for personal automation

    -- Profile information
    bio TEXT,
    timezone TEXT DEFAULT 'UTC',
    availability_hours INTEGER DEFAULT 40,

    -- Skills and preferences (stored as JSONB for flexibility)
    skills JSONB DEFAULT '[]'::jsonb,
    preferred_tasks JSONB DEFAULT '[]'::jsonb,
    links JSONB DEFAULT '{}'::jsonb,

    -- Profile document
    profile_doc_id TEXT,
    profile_url TEXT,

    -- Metadata
    onboarded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_hours CHECK (availability_hours >= 0 AND availability_hours <= 168)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON public.team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_email ON public.team_members(email);
CREATE INDEX IF NOT EXISTS idx_team_members_discord_username ON public.team_members(discord_username);
CREATE INDEX IF NOT EXISTS idx_team_members_clickup_user_id ON public.team_members(clickup_user_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_team_members_updated_at
    BEFORE UPDATE ON public.team_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;

-- Create policies

-- Allow users to read all team members (for Discord bot lookups)
CREATE POLICY "Team members are viewable by authenticated users"
    ON public.team_members
    FOR SELECT
    TO authenticated
    USING (true);

-- Allow users to update their own profile
CREATE POLICY "Users can update their own profile"
    ON public.team_members
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Allow service role to insert new team members (during onboarding)
CREATE POLICY "Service role can insert team members"
    ON public.team_members
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Allow service role to update any team member (for admin operations)
CREATE POLICY "Service role can update team members"
    ON public.team_members
    FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow service role to delete team members
CREATE POLICY "Service role can delete team members"
    ON public.team_members
    FOR DELETE
    TO service_role
    USING (true);

-- Add helpful comments
COMMENT ON TABLE public.team_members IS 'Centralized team member information for Alfred system';
COMMENT ON COLUMN public.team_members.user_id IS 'References auth.users - Supabase auth user ID';
COMMENT ON COLUMN public.team_members.discord_username IS 'Discord username for bot integration (unique)';
COMMENT ON COLUMN public.team_members.clickup_user_id IS 'ClickUp user ID for task management';
COMMENT ON COLUMN public.team_members.clickup_api_token IS 'Optional personal ClickUp API token for automation';
COMMENT ON COLUMN public.team_members.skills IS 'Array of skill objects: [{"name": "Python", "experience_level": "expert", "years": 5}]';
COMMENT ON COLUMN public.team_members.preferred_tasks IS 'Array of preferred task types';
COMMENT ON COLUMN public.team_members.links IS 'Object with external links: {"github": "url", "linkedin": "url"}';
