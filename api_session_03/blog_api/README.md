/api/v1
│
├── /users
│   ├── GET
│   ├── POST
│   │
│   └── /{user_id}
│       ├── GET
│       ├── PATCH
│       ├── DELETE
│       │
│       ├── /posts
│       │   └── GET
│       │
│       ├── /followers
│       │   └── GET
│       │
│       └── /following
│           ├── GET
│           ├── POST
│           └── /{target_user_id}
│               └── DELETE
│
├── /posts
│   ├── GET
│   ├── POST
│   │
│   └── /{post_id}
│       ├── GET
│       ├── PATCH
│       ├── DELETE
│       │
│       ├── /comments
│       │   ├── GET
│       │   ├── POST
│       │   │
│       │   └── /{comment_id}
│       │       ├── GET
│       │       ├── PATCH
│       │       └── DELETE
│       │
│       └── /tags
│           ├── GET
│           ├── POST
│           └── /{tag_id}
│               └── DELETE
│
└── /tags
    ├── GET
    ├── POST
    │
    └── /{tag_id}
        ├── GET
        ├── PATCH
        └── DELETE