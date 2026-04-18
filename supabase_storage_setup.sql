-- Run in Supabase SQL editor
-- Creates storage bucket + permissive policies for server-side backend usage.

insert into storage.buckets (id, name, public)
values ('generated-papers', 'generated-papers', false)
on conflict (id) do nothing;

-- generated_papers table policies (if RLS is enabled)
alter table public.generated_papers enable row level security;

drop policy if exists generated_papers_select_all on public.generated_papers;
create policy generated_papers_select_all
on public.generated_papers
for select
using (true);

drop policy if exists generated_papers_insert_all on public.generated_papers;
create policy generated_papers_insert_all
on public.generated_papers
for insert
with check (true);

drop policy if exists generated_papers_update_all on public.generated_papers;
create policy generated_papers_update_all
on public.generated_papers
for update
using (true)
with check (true);

-- student_feedback table policies (if RLS is enabled)
alter table public.student_feedback enable row level security;

drop policy if exists student_feedback_select_all on public.student_feedback;
create policy student_feedback_select_all
on public.student_feedback
for select
using (true);

drop policy if exists student_feedback_insert_all on public.student_feedback;
create policy student_feedback_insert_all
on public.student_feedback
for insert
with check (true);

-- storage object policies for generated-papers bucket
-- NOTE: these policies are broad; for production tighten them by owner/user claims.
drop policy if exists generated_papers_storage_select on storage.objects;
create policy generated_papers_storage_select
on storage.objects
for select
using (bucket_id = 'generated-papers');

drop policy if exists generated_papers_storage_insert on storage.objects;
create policy generated_papers_storage_insert
on storage.objects
for insert
with check (bucket_id = 'generated-papers');

drop policy if exists generated_papers_storage_update on storage.objects;
create policy generated_papers_storage_update
on storage.objects
for update
using (bucket_id = 'generated-papers')
with check (bucket_id = 'generated-papers');
