-- Prevent two teachers from receiving the same class invitation code.
ALTER TABLE `teacher_class`
  ADD UNIQUE KEY `uk_teacher_invite_code` (`invite_code`);
