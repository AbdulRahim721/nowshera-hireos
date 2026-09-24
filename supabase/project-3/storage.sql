insert into storage.buckets (id,name,public) values ('candidate-cvs','candidate-cvs',false) on conflict (id) do update set public=false;
drop policy if exists "candidate uploads own cv" on storage.objects;
create policy "candidate uploads own cv" on storage.objects for insert to authenticated with check(bucket_id='candidate-cvs' and (storage.foldername(name))[1]=auth.uid()::text);
drop policy if exists "candidate reads own cv" on storage.objects;
create policy "candidate reads own cv" on storage.objects for select to authenticated using(bucket_id='candidate-cvs' and (storage.foldername(name))[1]=auth.uid()::text);
drop policy if exists "candidate replaces own cv" on storage.objects;
create policy "candidate replaces own cv" on storage.objects for update to authenticated using(bucket_id='candidate-cvs' and (storage.foldername(name))[1]=auth.uid()::text) with check(bucket_id='candidate-cvs' and (storage.foldername(name))[1]=auth.uid()::text);
