# Publishing a Research Post

## Workflow

1. Create a folder under `research/` with a descriptive slug (this becomes the URL):
   ```
   research/my-post-title/
   ```

2. Add a `README.md` with a YAML front-matter block at the top:
   ```yaml
   ---
   title: "Your Post Title"
   description: "One or two sentences. Used as the meta description and listing teaser."
   date: 2026-06-01
   tags: [security, LLM, research]
   og_image: your-chart.png     # social preview image (optional — defaults to first image)
   draft: false                  # set to true to hide from listing
   ---
   ```

3. Write the body in standard Markdown after the front-matter block.
   - Reference images with `![descriptive alt text](filename.png)`
   - Drop all image files in the same folder
   - Use triple-backtick fences for code blocks

4. Preview locally (optional):
   ```sh
   pip install markdown Pygments PyYAML
   python build.py
   open research/my-post-title/index.html
   ```

5. Commit and push — GitHub Actions runs `build.py` during deploy. The post is live at:
   - `https://benedikt90.github.io/research/my-post-title/`
   - Listed on `https://benedikt90.github.io/research/`
   - Included in `sitemap.xml`

## Front-matter reference

| Field         | Required | Default                          |
|---------------|----------|----------------------------------|
| `title`       | no       | First `#` heading in the file    |
| `description` | no       | First paragraph (truncated)      |
| `date`        | no       | File modification time           |
| `tags`        | no       | *(none)*                         |
| `og_image`    | no       | First image found in the post    |
| `draft`       | no       | `false`                          |

## Notes

- The folder slug becomes the permanent URL — choose it carefully.
- Generated `index.html` files are gitignored; they live only in the deployed artifact.
- The listing page (`research/index.html`) is rebuilt on every deploy and sorted newest-first.
