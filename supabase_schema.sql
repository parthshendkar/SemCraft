-- Run this in Supabase SQL editor

create table if not exists public.generated_papers (
    id bigint generated always as identity primary key,
    owner_token text not null,
    subject text not null,
    semester text not null,
    department text not null,
    total_marks integer not null,
    paper_data jsonb not null,
    pdf_file_path text,
    created_at timestamptz not null default timezone('utc', now())
);

-- Make schema backward-compatible with older versions that used pc_number.
do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'generated_papers'
          and column_name = 'pc_number'
    )
    and not exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'generated_papers'
          and column_name = 'owner_token'
    ) then
        alter table public.generated_papers rename column pc_number to owner_token;
    end if;

    if not exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'generated_papers'
          and column_name = 'owner_token'
    ) then
        alter table public.generated_papers add column owner_token text;
    end if;

    if not exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'generated_papers'
          and column_name = 'pdf_file_path'
    ) then
        alter table public.generated_papers add column pdf_file_path text;
    end if;
end
$$;

create index if not exists idx_generated_papers_owner_token_created_at
    on public.generated_papers(owner_token, created_at desc);

-- Optional migration for older table versions:
-- alter table public.generated_papers rename column pc_number to owner_token;

create table if not exists public.student_feedback (
    id bigint generated always as identity primary key,
    name text not null,
    department text not null,
    prn text not null,
    feedback text not null,
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_student_feedback_created_at
    on public.student_feedback(created_at desc);
