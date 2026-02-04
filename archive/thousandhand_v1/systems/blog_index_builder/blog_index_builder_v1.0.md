# SYSTEM: BlogIndexBuilder
## Version 1.0

---

## PURPOSE

Generate the main blog index page (/blog) that lists all published articles with navigation, filtering, and pagination.

---

## INTERFACE

### Input Schema

```json
{
  "index_entries_path": "string - Path to JSON file with all blog entries",
  "output_dir": "string - Where to write index.html",
  "site_config": {
    "base_url": "string",
    "blog_path": "string",
    "posts_per_page": "number - default: 10",
    "site_name": "string"
  }
}
```

### Output Schema

```json
{
  "success": "boolean",
  "pages_generated": "number",
  "index_path": "string - Path to main index",
  "pagination_paths": ["string"] - Paths to page-2, page-3, etc.
}
```

---

## PROCESS

### Step 1: Load All Entries
- Read index entries JSON
- Sort by date (newest first)
- Group by category if applicable

### Step 2: Build Main Index Page
Structure:
```html
<main class="blog-index">
  <header>
    <h1>Man vs Health Blog</h1>
    <p>No-BS insights on metabolic health for men over 40</p>
  </header>
  
  <section class="featured">
    <!-- Most recent or pinned post, larger card -->
  </section>
  
  <section class="posts">
    <!-- Grid of post cards -->
    <article class="post-card">
      <img src="{thumb}" alt="">
      <div class="content">
        <time>{date}</time>
        <h2><a href="{url}">{title}</a></h2>
        <p>{excerpt}</p>
      </div>
    </article>
    ...
  </section>
  
  <nav class="pagination">
    <!-- Page numbers -->
  </nav>
</main>
```

### Step 3: Generate Pagination
If more than `posts_per_page`:
- Create /blog/page/2/, /blog/page/3/, etc.
- Each page has same structure, different posts
- Include prev/next navigation

### Step 4: Generate RSS Feed
Create /blog/feed.xml:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Man vs Health Blog</title>
    <link>{base_url}/blog</link>
    <description>...</description>
    <item>
      <title>{post_title}</title>
      <link>{post_url}</link>
      <pubDate>{date}</pubDate>
      <description>{excerpt}</description>
    </item>
    ...
  </channel>
</rss>
```

### Step 5: Generate Sitemap Entries
Append blog URLs to sitemap.xml:
```xml
<url>
  <loc>{full_url}</loc>
  <lastmod>{date}</lastmod>
  <changefreq>monthly</changefreq>
</url>
```

---

## CONSTRAINTS

- Maximum 10 posts per page (configurable)
- Index must load fast (lazy load images below fold)
- Mobile-first grid layout
- Consistent with site design

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-17 | Initial specification |
