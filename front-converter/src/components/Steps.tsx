type StepIconType = "link" | "protocol" | "download";

function StepIcon({ type }: { type: StepIconType }) {
	if (type === "link") {
		return (
			<svg viewBox="0 0 24 24" className="step-icon-svg" role="presentation">
				<path d="M10.2 7.8h-2a4.6 4.6 0 1 0 0 9.2h2" />
				<path d="M13.8 7.8h2a4.6 4.6 0 0 1 0 9.2h-2" />
				<path d="M8.8 12h6.4" />
			</svg>
		);
	}

	if (type === "protocol") {
		return (
			<svg viewBox="0 0 24 24" className="step-icon-svg" role="presentation">
				<rect x="3" y="9.2" width="2.4" height="7.2" rx="0.6" />
				<rect x="7.2" y="6.8" width="2.4" height="9.6" rx="0.6" />
				<rect x="11.4" y="4.8" width="2.4" height="11.6" rx="0.6" />
				<rect x="15.6" y="6.2" width="2.4" height="10.2" rx="0.6" />
			</svg>
		);
	}

	return (
		<svg viewBox="0 0 24 24" className="step-icon-svg" role="presentation">
			<circle cx="12" cy="11" r="5.8" />
			<path d="M12 8.2v5" />
			<path d="M9.8 13.4 12 15.8l2.2-2.4" />
			<path d="M7 18.8h10" />
		</svg>
	);
}

const STEPS = [
	{
		number: "01",
		title: "INTERCEPTAR ENLACE",
		description:
			"Copia la URL de origen de la red e introdúcela en nuestra interfaz cinética segura.",
		icon: "link" as const,
	},
	{
		number: "02",
		title: "EJECUTAR PROTOCOLO",
		description:
			"Nuestros servidores evitan paquetes de datos innecesarios, aislando las frecuencias de audio de alta definición.",
		icon: "protocol" as const,
	},
	{
		number: "03",
		title: "RECUPERAR FLUJO",
		description:
			"Descarga tu archivo MP3 localizado al instante. Sin latencia. Sin artefactos de compresión. Solo datos.",
		icon: "download" as const,
	},
];

export default function Steps() {
	return (
		<section id="caracteristicas" className="process-steps" aria-label="Pasos del convertidor">
			<div className="steps-container">
				{STEPS.map((step) => (
					<article key={step.number} className="step-card">
						<span className="step-number" aria-hidden="true">
							{step.number}
						</span>

						<span className="step-icon" aria-hidden="true">
							<StepIcon type={step.icon} />
						</span>

						<h3 className="step-title">{step.title}</h3>
						<p className="step-description">{step.description}</p>
					</article>
				))}
			</div>
		</section>
	);
}
