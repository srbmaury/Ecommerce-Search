import html


def build_html(summary, cluster_counts, top_queries):
    html_out = "<h2>A/B Group Analytics</h2><table border=1>"
    html_out += (
        "<tr><th>Group</th><th>Users</th><th>Searches</th>"
        "<th>Clicks</th><th>Add to Cart</th><th>CTR</th><th>Conversion</th></tr>"
    )

    for g, s in summary.items():
        html_out += (
            f"<tr><td>{g}</td><td>{s['users']}</td>"
            f"<td>{s['searches']}</td><td>{s['clicks']}</td>"
            f"<td>{s['add_to_cart']}</td>"
            f"<td>{s['CTR']}</td><td>{s['Conversion']}</td></tr>"
        )

    html_out += "</table>"

    if cluster_counts:
        html_out += "<h2>Cluster Sizes</h2><table border=1>"
        for c, n in cluster_counts.items():
            html_out += f"<tr><td>{c}</td><td>{n}</td></tr>"
        html_out += "</table>"

    html_out += "<h2>Top Queries</h2><table border=1>"
    for q, c in top_queries.items():
        html_out += f"<tr><td>{html.escape(str(q))}</td><td>{c}</td></tr>"
    html_out += "</table>"

    return html_out
