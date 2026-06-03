import { useEffect, useState, type FormEvent } from "react";

type Channel = {
  id: number;
  title: string;
  username: string | null;
  url: string;
  category: string;
  is_active: boolean;
  created_at: string;
};

type Entity = {
  id: number;
  entity_text: string;
  normalized_text: string;
  entity_type: string;
  source: string;
  confidence: number | null;
};

type Trend = {
  entity: string;
  entity_type: string;
  mentions_count: number;
  channels_count: number;
  total_views: number;
  total_reactions: number;
  growth_7d: number | null;
  growth_30d: number | null;
  trend_score: number;
  new_trend: boolean;
  latest_date: string;
};

type Post = {
  id: number;
  telegram_message_id: number;
  channel_id: number;
  channel_title: string;
  post_date: string;
  text: string;
  views: number;
  forwards: number;
  reactions_count: number;
  url: string;
  entities: Entity[];
};

type TrendDetail = {
  entity: string;
  entity_type: string;
  sources: string[];
  design_potential: string;
  stats: Array<{
    date: string;
    mentions_count: number;
    channels_count: number;
    total_views: number;
    total_reactions: number;
    growth_7d: number | null;
    growth_30d: number | null;
    trend_score: number;
    new_trend: boolean;
  }>;
  channels: string[];
  related_entities: string[];
  posts: Array<{
    channel_title: string;
    post_date: string;
    text: string;
    url: string;
  }>;
};

type Settings = {
  default_posts_limit: number;
  schedule_enabled: boolean;
  schedule_hour_utc: number;
  last_collected_at: string | null;
};

type Bootstrap = {
  settings: Settings;
  channels: Channel[];
  top_trends: Trend[];
};

type CollectionResult = {
  collected_posts: number;
  extracted_entities: number;
  processed_channels: number;
  started_at: string;
  finished_at: string;
  warnings: string[];
};

type ShirtOfDay = {
  current: {
    id: number;
    created_at: string;
    trend_entity: string;
    trend_entity_type: string;
    trend_score: number;
    trend_growth_7d: number | null;
    description: string;
    brief_prompt: string;
  } | null;
  history: Array<{
    id: number;
    created_at: string;
    trend_entity: string;
    trend_entity_type: string;
    trend_score: number;
    trend_growth_7d: number | null;
    description: string;
    brief_prompt: string;
  }>;
};

type Route =
  | { name: "home" }
  | { name: "posts" }
  | { name: "channels" }
  | { name: "settings" }
  | { name: "shirt-of-day" }
  | { name: "trend"; entity: string };

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

function parseRoute(pathname: string): Route {
  const clean = pathname.replace(/\/+$/, "");
  if (clean.endsWith("/posts")) return { name: "posts" };
  if (clean.endsWith("/channels")) return { name: "channels" };
  if (clean.endsWith("/settings")) return { name: "settings" };
  if (clean.endsWith("/shirt-of-day")) return { name: "shirt-of-day" };
  const trendMatch = clean.match(/\/trends\/(.+)$/);
  if (trendMatch) return { name: "trend", entity: decodeURIComponent(trendMatch[1]) };
  return { name: "home" };
}

function navigate(path: string) {
  window.history.pushState(null, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function formatGrowth(value: number | null, isNew: boolean) {
  if (value === null) return isNew ? "new" : "n/a";
  return `${value > 0 ? "+" : ""}${value.toFixed(0)}%`;
}

function formatDate(value: string | null) {
  if (!value) return "еще не запускалось";
  return new Date(value).toLocaleString("ru-RU");
}

function App() {
  const [route, setRoute] = useState<Route>(() => parseRoute(window.location.pathname));
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [trendDetail, setTrendDetail] = useState<TrendDetail | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [shirtOfDay, setShirtOfDay] = useState<ShirtOfDay | null>(null);
  const [channelIdentifier, setChannelIdentifier] = useState("");
  const [channelCategory, setChannelCategory] = useState("general");
  const [postsLimit, setPostsLimit] = useState("10");
  const [entityFilter, setEntityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [briefPrompt, setBriefPrompt] = useState<string | null>(null);

  useEffect(() => {
    const onPopState = () => setRoute(parseRoute(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  async function loadBootstrap() {
    const data = await request<Bootstrap>("/public/bootstrap");
    setBootstrap(data);
    setSettings(data.settings);
    setTrends(data.top_trends);
    setPostsLimit(String(data.settings.default_posts_limit));
  }

  async function loadShirtOfDay() {
    const data = await request<ShirtOfDay>("/public/shirt-of-day");
    setShirtOfDay(data);
  }

  useEffect(() => {
    loadBootstrap().catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (route.name === "posts") {
      request<Post[]>(`/public/posts?limit=50${entityFilter ? `&entity=${encodeURIComponent(entityFilter)}` : ""}`)
        .then(setPosts)
        .catch((err) => setError(err.message));
    }
    if (route.name === "trend") {
      request<TrendDetail>(`/public/trends/${encodeURIComponent(route.entity)}`)
        .then(setTrendDetail)
        .catch((err) => setError(err.message));
    }
    if (route.name === "settings") {
      request<Settings>("/public/settings")
        .then(setSettings)
        .catch((err) => setError(err.message));
    }
    if (route.name === "shirt-of-day") {
      loadShirtOfDay().catch((err) => setError(err.message));
    }
  }, [route, entityFilter]);

  async function refreshTrends() {
    const query = new URLSearchParams({ days: "7", limit: "20" });
    if (typeFilter) query.set("entity_type", typeFilter);
    if (categoryFilter) query.set("category", categoryFilter);
    const data = await request<Trend[]>(`/public/trends?${query.toString()}`);
    setTrends(data);
  }

  useEffect(() => {
    refreshTrends().catch((err) => setError(err.message));
  }, [typeFilter, categoryFilter]);

  async function handleCollect() {
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await request<CollectionResult>(`/public/collect?limit=${Number(postsLimit) || 10}`, { method: "POST" });
      setMessage(
        `Постов: ${result.collected_posts}, сущностей: ${result.extracted_entities}, каналов: ${result.processed_channels}`,
      );
      if (result.warnings.length) {
        setError(result.warnings.join(" | "));
      }
      await loadBootstrap();
      await refreshTrends();
      await loadShirtOfDay().catch(() => undefined);
      if (route.name === "posts") {
        setPosts(await request<Post[]>("/public/posts?limit=50"));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAddChannel(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await request<Channel>("/public/channels", {
        method: "POST",
        body: JSON.stringify({ identifier: channelIdentifier, category: channelCategory }),
      });
      setChannelIdentifier("");
      await loadBootstrap();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function toggleChannel(channel: Channel) {
    await request<Channel>(`/public/channels/${channel.id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !channel.is_active }),
    });
    await loadBootstrap();
  }

  async function saveSettings(event: FormEvent) {
    event.preventDefault();
    if (!settings) return;
    setLoading(true);
    try {
      const updated = await request<Settings>("/public/settings", {
        method: "PUT",
        body: JSON.stringify(settings),
      });
      setSettings(updated);
      setMessage("Настройки сохранены");
      await loadBootstrap();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function openBrief(entity: string) {
    const result = await request<{ prompt: string }>(`/public/trends/${encodeURIComponent(entity)}/brief`, {
      method: "POST",
    });
    setBriefPrompt(result.prompt);
  }

  const categories = Array.from(new Set((bootstrap?.channels ?? []).map((item) => item.category))).sort();
  const entityTypes = Array.from(new Set(trends.map((item) => item.entity_type))).sort();

  return (
    <div className="shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />
      <header className="hero">
        <div>
          <p className="eyebrow">Trend Monitor / Saint Petersburg</p>
          <h1>Мониторинг Telegram-трендов для дизайнерских футболок</h1>
          <p className="subtitle">
            Каналы, сущности, локальные темы СПб, быстрые сигналы роста и заготовка для будущих дизайнерских брифов.
          </p>
        </div>
        <nav className="nav">
          <button onClick={() => navigate("/app")}>Главная</button>
          <button onClick={() => navigate("/app/shirt-of-day")}>Футболка дня</button>
          <button onClick={() => navigate("/app/posts")}>Посты</button>
          <button onClick={() => navigate("/app/channels")}>Каналы</button>
          <button onClick={() => navigate("/app/settings")}>Настройки</button>
        </nav>
      </header>

      <main className="layout">
        <aside className="panel panel-side">
          <h2>Сбор данных</h2>
          <label>
            Количество постов
            <input value={postsLimit} onChange={(e) => setPostsLimit(e.target.value)} inputMode="numeric" />
          </label>
          <button className="primary" disabled={loading} onClick={handleCollect}>
            {loading ? "Сбор..." : "Собрать данные"}
          </button>
          <p className="meta">Последний запуск: {formatDate(settings?.last_collected_at ?? bootstrap?.settings.last_collected_at ?? null)}</p>

          <h3>Фильтры трендов</h3>
          <label>
            Тип сущности
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
              <option value="">Все</option>
              {entityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>
          <label>
            Категория канала
            <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
              <option value="">Все</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
          {message ? <div className="notice success">{message}</div> : null}
          {error ? <div className="notice error">{error}</div> : null}
        </aside>

        <section className="panel panel-main">
          {route.name === "home" && (
            <>
              <div className="section-head">
                <div>
                  <p className="eyebrow">Top 20 / 7 days</p>
                  <h2>Тренды последних 7 дней</h2>
                </div>
              </div>
              <div className="trend-grid">
                {trends.map((trend) => (
                  <article key={`${trend.entity}-${trend.entity_type}`} className="trend-card">
                    <div className="trend-topline">
                      <span className="pill">{trend.entity_type}</span>
                      <span className={trend.new_trend ? "growth growth-new" : "growth"}>{formatGrowth(trend.growth_7d, trend.new_trend)}</span>
                    </div>
                    <h3>{trend.entity}</h3>
                    <p className="stats-line">
                      Каналов: {trend.channels_count} · Упоминаний: {trend.mentions_count}
                    </p>
                    <p className="stats-line">Score: {trend.trend_score.toFixed(1)}</p>
                    <div className="card-actions">
                      <button onClick={() => navigate(`/app/trends/${encodeURIComponent(trend.entity)}`)}>Открыть</button>
                      <button onClick={() => openBrief(trend.entity)}>Создать бриф</button>
                    </div>
                  </article>
                ))}
              </div>
            </>
          )}

          {route.name === "shirt-of-day" && (
            <>
              <div className="section-head">
                <div>
                  <p className="eyebrow">Shirt Of The Day</p>
                  <h2>История брифов для печати</h2>
                </div>
              </div>
              {shirtOfDay?.current ? (
                <>
                <article className="shirt-brief">
                  <p className="eyebrow">Current top trend</p>
                  <h3>{shirtOfDay.current.trend_entity}</h3>
                  <p className="stats-line">
                    Тип: {shirtOfDay.current.trend_entity_type} · Score: {shirtOfDay.current.trend_score.toFixed(1)} · Рост:{" "}
                    {formatGrowth(shirtOfDay.current.trend_growth_7d, false)}
                  </p>
                  <p>{shirtOfDay.current.description}</p>
                  <div className="card-actions">
                    <button onClick={() => navigate(`/app/trends/${encodeURIComponent(shirtOfDay.current.trend_entity)}`)}>Открыть тренд</button>
                    <button onClick={() => setBriefPrompt(shirtOfDay.current!.brief_prompt)}>Открыть бриф</button>
                  </div>
                </article>
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Last 20 entries</p>
                    <h2>История брифов</h2>
                  </div>
                </div>
                <div className="brief-history-table">
                  <div className="brief-history-head">Дата/время</div>
                  <div className="brief-history-head">Тренд</div>
                  <div className="brief-history-head">Краткое описание</div>
                  {shirtOfDay.history.map((item) => (
                    <button key={item.id} className="brief-history-row" onClick={() => setBriefPrompt(item.brief_prompt)}>
                      <span className="brief-history-cell">{formatDate(item.created_at)}</span>
                      <span className="brief-history-cell brief-history-trend">{item.trend_entity}</span>
                      <span className="brief-history-cell">{item.description}</span>
                    </button>
                  ))}
                </div>
                </>
              ) : (
                <div className="detail-box">
                  <p>Недостаточно данных. Сначала соберите посты, затем здесь появится история автоматически созданных брифов.</p>
                </div>
              )}
            </>
          )}

          {route.name === "trend" && trendDetail && (
            <>
              <div className="section-head">
                <div>
                  <p className="eyebrow">Trend Detail</p>
                  <h2>{trendDetail.entity}</h2>
                </div>
                <button onClick={() => openBrief(trendDetail.entity)}>Создать бриф</button>
              </div>
              <div className="detail-grid">
                <div className="detail-box">
                  <h3>Сводка</h3>
                  <p>Тип: {trendDetail.entity_type}</p>
                  <p>Источники: {trendDetail.sources.join(", ") || "нет"}</p>
                  <p>{trendDetail.design_potential}</p>
                </div>
                <div className="detail-box">
                  <h3>Каналы</h3>
                  <p>{trendDetail.channels.join(", ") || "нет"}</p>
                </div>
                <div className="detail-box">
                  <h3>Связанные сущности</h3>
                  <p>{trendDetail.related_entities.join(", ") || "нет"}</p>
                </div>
              </div>
              <div className="chart-box">
                <h3>Динамика по дням</h3>
                <div className="chart">
                  {trendDetail.stats.map((point) => (
                    <div key={point.date} className="chart-row">
                      <span>{point.date}</span>
                      <div className="bar-wrap">
                        <div className="bar" style={{ width: `${Math.min(100, point.mentions_count * 12)}%` }} />
                      </div>
                      <strong>{point.mentions_count}</strong>
                    </div>
                  ))}
                </div>
              </div>
              <div className="detail-box">
                <h3>Примеры постов</h3>
                {trendDetail.posts.map((item, index) => (
                  <article key={`${item.url}-${index}`} className="post-card">
                    <p className="post-meta">
                      {item.channel_title} · {formatDate(item.post_date)}
                    </p>
                    <p>{item.text}</p>
                    {item.url ? (
                      <a href={item.url} target="_blank" rel="noreferrer">
                        Открыть пост
                      </a>
                    ) : null}
                  </article>
                ))}
              </div>
            </>
          )}

          {route.name === "posts" && (
            <>
              <div className="section-head">
                <div>
                  <p className="eyebrow">Latest Posts</p>
                  <h2>Последние собранные посты</h2>
                </div>
                <input
                  placeholder="Фильтр по сущности"
                  value={entityFilter}
                  onChange={(e) => setEntityFilter(e.target.value)}
                />
              </div>
              {posts.map((post) => (
                <article key={post.id} className="post-card">
                  <p className="post-meta">
                    {post.channel_title} · {formatDate(post.post_date)} · 👁 {post.views} · ↗ {post.forwards} · ❤ {post.reactions_count}
                  </p>
                  <p>{post.text}</p>
                  <div className="entity-list">
                    {post.entities.map((entity) => (
                      <button
                        key={entity.id}
                        className="pill pill-button"
                        onClick={() => navigate(`/app/trends/${encodeURIComponent(entity.normalized_text)}`)}
                      >
                        {entity.normalized_text} / {entity.entity_type}
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </>
          )}

          {route.name === "channels" && (
            <>
              <div className="section-head">
                <div>
                  <p className="eyebrow">Sources</p>
                  <h2>Telegram-каналы</h2>
                </div>
              </div>
              <form className="channel-form" onSubmit={handleAddChannel}>
                <input
                  placeholder="@channel или https://t.me/channel"
                  value={channelIdentifier}
                  onChange={(e) => setChannelIdentifier(e.target.value)}
                />
                <input placeholder="Категория" value={channelCategory} onChange={(e) => setChannelCategory(e.target.value)} />
                <button type="submit">Добавить</button>
              </form>
              <div className="channel-list">
                {(bootstrap?.channels ?? []).map((channel) => (
                  <article key={channel.id} className="channel-card">
                    <div>
                      <h3>{channel.title}</h3>
                      <p>
                        {channel.category} · {channel.username ? `@${channel.username}` : channel.url}
                      </p>
                    </div>
                    <button onClick={() => toggleChannel(channel)}>{channel.is_active ? "Отключить" : "Включить"}</button>
                  </article>
                ))}
              </div>
            </>
          )}

          {route.name === "settings" && settings && (
            <>
              <div className="section-head">
                <div>
                  <p className="eyebrow">Schedule</p>
                  <h2>Настройки сбора</h2>
                </div>
              </div>
              <form className="settings-form" onSubmit={saveSettings}>
                <label>
                  Постов по умолчанию
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={settings.default_posts_limit}
                    onChange={(e) => setSettings({ ...settings, default_posts_limit: Number(e.target.value) })}
                  />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={settings.schedule_enabled}
                    onChange={(e) => setSettings({ ...settings, schedule_enabled: e.target.checked })}
                  />
                  Ежедневный запуск включен
                </label>
                <label>
                  Час запуска UTC
                  <input
                    type="number"
                    min={0}
                    max={23}
                    value={settings.schedule_hour_utc}
                    onChange={(e) => setSettings({ ...settings, schedule_hour_utc: Number(e.target.value) })}
                  />
                </label>
                <button type="submit">Сохранить</button>
              </form>
            </>
          )}
        </section>
      </main>

      {briefPrompt ? (
        <div className="modal-backdrop" onClick={() => setBriefPrompt(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="section-head">
              <h2>Промпт для дизайнера</h2>
              <button onClick={() => setBriefPrompt(null)}>Закрыть</button>
            </div>
            <pre>{briefPrompt}</pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
