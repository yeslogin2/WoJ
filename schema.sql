pragma foreign_keys = ON;

drop table if exists users;
create table users(
    userId integer primary key autoincrement,
    username nvarchar(30) not null unique,
    password char(32)
);

drop table if exists diaries;
create table diaries(
    id integer primary key autoincrement,
    userId integer,
    title string not null,
    text string not null,
    date string not null,
    foreign key(userId) references users(userId) on delete cascade
);
