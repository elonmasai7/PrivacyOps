type ModulePageProps = {
  title: string;
  subtitle: string;
  emptyHeading: string;
  emptyBody: string;
  cta?: string;
};

export function ModulePage(props: ModulePageProps) {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: "var(--font-headline)" }}>
          {props.title}
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">{props.subtitle}</p>
      </header>
      <section className="empty-state">
        <h2 className="text-lg font-semibold text-slate-800">{props.emptyHeading}</h2>
        <p className="mt-2 text-sm text-slate-600">{props.emptyBody}</p>
        {props.cta ? (
          <button className="mt-4 rounded-md bg-baobab-700 px-4 py-2 text-sm font-medium text-white">{props.cta}</button>
        ) : null}
      </section>
    </div>
  );
}
