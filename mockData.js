// ============================================================
// READWISE — All Mock Data (Thesis Prototype)
// ============================================================
const MOCK = {
  students: [
    { id:"s1", name:"Juan Dela Cruz",  grade:"7", section:"Sampaguita", classLevel:"HARD",     preScore:58 },
    { id:"s2", name:"Maria Santos",    grade:"7", section:"Sampaguita", classLevel:"MODERATE", preScore:72 },
    { id:"s3", name:"Carlo Reyes",     grade:"7", section:"Sampaguita", classLevel:"EASY",     preScore:45 }
  ],
  teacher: { name:"Ms. Ana Villanueva", subject:"Grade 7 English", school:"Pulo National High School" },
  passages: [
    { id:"p1", title:"The Water Cycle",                      label:"EASY",     genre:"Expository", words:120, time:2,
      text:`The water cycle is the continuous movement of water through Earth's systems. It begins when the sun heats water in oceans, rivers, and lakes, causing it to evaporate and rise into the atmosphere as water vapor. As this vapor cools at higher altitudes, it condenses around tiny dust particles to form clouds. When enough water droplets gather, they fall back to Earth as precipitation — rain, snow, sleet, or hail. Some water flows across the land as runoff into rivers and back to the ocean. Some soaks into the ground to become groundwater. Plants also return water to the air through a process called transpiration. Together, these processes form the never-ending water cycle that supports all life on our planet.` },
    { id:"p2", title:"The Life of Jose Rizal",               label:"MODERATE", genre:"Narrative",  words:210, time:3,
      text:`José Protasio Rizal Mercado y Alonso Realonda was born on June 19, 1861, in Calamba, Laguna, Philippines. He was the seventh of eleven children of Francisco Rizal Mercado II and Teodora Alonso Realonda. From an early age, he showed remarkable intelligence and a deep love for learning. Rizal was educated at the Ateneo Municipal de Manila, where he excelled in academics and the arts. He later pursued medicine at the University of Santo Tomas and continued his studies in Spain. Abroad, Rizal became acutely aware of the injustices faced by Filipinos under Spanish colonial rule. He channeled his passion into writing, producing his two legendary novels — Noli Me Tangere (1887) and El Filibusterismo (1891) — which stirred the spirit of Filipino nationalism. He also founded La Liga Filipina. His activism led to his arrest and execution by firing squad at Bagumbayan on December 30, 1896. He was only 35 years old. Today, José Rizal is honored as the national hero of the Philippines.` },
    { id:"p3", title:"Climate Change and Its Effects",        label:"HARD",     genre:"Expository", words:310, time:4,
      text:`Climate change refers to long-term shifts in global temperatures and weather patterns. While some climate variation is natural, scientific evidence overwhelmingly shows that human activities — particularly the burning of fossil fuels such as coal, oil, and natural gas — have been the dominant cause since the mid-20th century. These activities release large amounts of carbon dioxide (CO₂) and other greenhouse gases into the atmosphere. The greenhouse effect occurs when these gases trap heat from the sun, preventing it from escaping back into space, causing global warming.\n\nThe consequences are wide-ranging and severe. Rising temperatures cause polar ice caps and glaciers to melt, contributing to sea-level rise that threatens low-lying coastal areas. The Philippines, being an archipelago, is particularly vulnerable to flooding, storm surges, and intensification of typhoons. Warmer ocean temperatures fuel stronger tropical cyclones. Changes in rainfall patterns affect agricultural productivity, leading to food and water insecurity. Coral reefs are bleaching and dying due to ocean acidification.\n\nBiodiversity loss is another critical consequence. Many species cannot adapt quickly enough to changing habitats. Climate change also poses public health risks: the spread of vector-borne diseases like dengue fever is expected to increase as warmer climates expand mosquito habitats. Addressing climate change requires global cooperation, renewable energy transition, forest protection, and sustainable agriculture.` },
    { id:"p4", title:"The Little Prince Summary",            label:"EASY",     genre:"Narrative",  words:140, time:2,
      text:`The Little Prince is a beloved novella by Antoine de Saint-Exupéry, first published in 1943. The story follows a young prince who travels from his tiny home planet to various asteroids and eventually to Earth. On each planet, he meets peculiar grown-ups who represent human flaws — vanity, greed, and blind authority. On Earth, the prince befriends a pilot stranded in the Sahara desert and a wise fox who teaches him: "One sees clearly only with the heart; what is essential is invisible to the eye." The little prince tends to a single rose on his home planet, which he learns to cherish despite her flaws. The story is a gentle reminder that the things that truly matter — love, friendship, and wonder — cannot be seen with the eyes alone.` },
    { id:"p5", title:"Philippine Biodiversity",              label:"MODERATE", genre:"Expository", words:195, time:3,
      text:`The Philippines is one of the world's 17 megadiverse countries, harboring extraordinary variety of plant and animal species. Its unique geographic position in Southeast Asia, combined with thousands of islands and diverse ecosystems — tropical rainforests, mangroves, coral reefs, and mountain ranges — has made it a global hotspot for biodiversity. Scientists estimate the country is home to more than 52,000 species of plants and animals, many of which are endemic — found nowhere else on Earth. The Philippine eagle, the tamaraw, and the tarsier are iconic endemic species. The Tubbataha Reef Natural Park is a UNESCO World Heritage Site and one of the world's finest coral reef ecosystems. Despite this, Philippine biodiversity faces serious threats: deforestation, illegal wildlife trade, coral reef destruction, and climate change. Conservation programs and environmental education in schools play key roles in protecting these natural treasures.` },
    { id:"p6", title:"Constitutional Rights of Citizens",    label:"HARD",     genre:"Expository", words:350, time:5,
      text:`The Constitution of the Philippines, ratified in 1987 following the People Power Revolution, is the supreme law of the land. It establishes the framework of the Philippine government and enumerates fundamental rights every Filipino citizen is entitled to. These rights — the Bill of Rights — are enshrined in Article III and protect individuals from state abuses.\n\nAmong the most fundamental rights is the right to life, liberty, and property. No person shall be deprived of these without due process of law — which has two dimensions: substantive due process (laws must be fair and reasonable) and procedural due process (legal procedures must be just). The equal protection clause mandates no person shall be discriminated against by law.\n\nThe Constitution guarantees freedom of speech, expression, and the press. Citizens may voice opinions, criticize policies, and engage in peaceful assembly. These freedoms are essential to democracy, allowing citizens to hold leaders accountable. However, they are not absolute — they are limited when they infringe on others' rights or pose clear and present danger.\n\nThe right against unreasonable searches and seizures protects citizens' privacy. Law enforcement must obtain a valid warrant before searching or arresting. Evidence gathered illegally is inadmissible under the exclusionary rule. Arrested citizens must be informed of their Miranda rights — the right to remain silent and the right to counsel.\n\nUnderstanding constitutional rights is a civic responsibility. An informed citizenry is the cornerstone of democracy.` }
  ],
  questions: {
    p1:[
      { q:"What process causes water to rise into the atmosphere?",    opts:["Condensation","Evaporation","Precipitation","Transpiration"], ans:1 },
      { q:"What forms when water vapor cools at high altitudes?",       opts:["Rain","Ice","Clouds","Fog"], ans:2 },
      { q:"Which term describes water flowing across land into rivers?",opts:["Transpiration","Evaporation","Groundwater","Runoff"], ans:3 }
    ],
    p2:[
      { q:"Where was Jose Rizal born?",                      opts:["Manila","Batangas","Calamba, Laguna","Cebu"], ans:2 },
      { q:"What was Rizal's first novel?",                   opts:["El Filibusterismo","Noli Me Tangere","Mi Ultimo Adios","La Solidaridad"], ans:1 },
      { q:"What civic organization did Rizal found?",        opts:["Katipunan","La Liga Filipina","Propaganda Movement","Ilustrado Society"], ans:1 }
    ],
    p3:[
      { q:"What is the main cause of climate change?",                  opts:["Volcanic eruptions","Human activities","Ocean currents","Solar flares"], ans:1 },
      { q:"Which gas is primarily responsible for the greenhouse effect?",opts:["Oxygen","Nitrogen","Carbon Dioxide","Hydrogen"], ans:2 },
      { q:"Which is a consequence of climate change mentioned in the passage?",opts:["More snowfall in deserts","Sea-level rise","Decreased typhoons","Lower ocean temperatures"], ans:1 }
    ],
    p4:[
      { q:"Who wrote The Little Prince?",                               opts:["Victor Hugo","Antoine de Saint-Exupéry","Jules Verne","Albert Camus"], ans:1 },
      { q:"What does the fox teach the little prince?",                 opts:["How to survive alone","One sees clearly only with the heart","Money is important","Never trust strangers"], ans:1 },
      { q:"What does the little prince tend to on his home planet?",    opts:["A tree","A garden","A single rose","A fountain"], ans:2 }
    ],
    p5:[
      { q:"How many megadiverse countries are there in the world?",    opts:["10","17","25","30"], ans:1 },
      { q:"Which reef is a UNESCO World Heritage Site?",               opts:["Palawan Reef","Tubbataha Reef Natural Park","Apo Island","Camiguin Reef"], ans:1 },
      { q:"Which is an endemic Philippine species mentioned?",         opts:["Sea turtle","Philippine eagle","Blue whale","Komodo dragon"], ans:1 }
    ],
    p6:[
      { q:"In which article are the Bill of Rights found?",            opts:["Article I","Article II","Article III","Article IV"], ans:2 },
      { q:"What rule makes evidence from illegal searches inadmissible?",opts:["Miranda rule","Exclusionary rule","Due process rule","Equal protection rule"], ans:1 },
      { q:"What are the two dimensions of due process?",               opts:["Civil and criminal","Procedural and substantive","Formal and informal","Written and oral"], ans:1 }
    ]
  },
  shortAnswer: {
    p3:"In your own words, explain one effect of climate change on the Philippines.",
    p6:"Explain what 'due process of law' means in your own words."
  },
  weeklyProgress: {
    s1:[
      { week:1, score:55, difficulty:"HARD",     recommendation:"Maintain" },
      { week:2, score:48, difficulty:"HARD",     recommendation:"Step DOWN to MODERATE" },
      { week:3, score:65, difficulty:"MODERATE", recommendation:"Maintain" },
      { week:4, score:71, difficulty:"MODERATE", recommendation:"Maintain" }
    ],
    s2:[
      { week:1, score:70, difficulty:"MODERATE", recommendation:"Maintain" },
      { week:2, score:75, difficulty:"MODERATE", recommendation:"Step UP to HARD" },
      { week:3, score:68, difficulty:"HARD",     recommendation:"Maintain" },
      { week:4, score:72, difficulty:"HARD",     recommendation:"Maintain" }
    ],
    s3:[
      { week:1, score:42, difficulty:"EASY",     recommendation:"Maintain" },
      { week:2, score:50, difficulty:"EASY",     recommendation:"Maintain" },
      { week:3, score:55, difficulty:"EASY",     recommendation:"Step UP to MODERATE" },
      { week:4, score:48, difficulty:"MODERATE", recommendation:"Step DOWN to EASY" }
    ]
  }
};

// Helpers
function getStudent(id)       { return MOCK.students.find(s=>s.id===id); }
function getPassage(id)       { return MOCK.passages.find(p=>p.id===id); }
function getCurrentStudent()  { return getStudent(sessionStorage.getItem("studentId")||"s1"); }
function levelColor(l)        { return l==="EASY"?"#2e7d5e":l==="MODERATE"?"#c97b2a":"#c0392b"; }
function levelBg(l)           { return l==="EASY"?"#d4edda":l==="MODERATE"?"#fff3cd":"#fde8e8"; }
function badgeClass(l)        { return l==="EASY"?"badge-easy":l==="MODERATE"?"badge-moderate":"badge-hard"; }
function getAssignedPassage(s){ return MOCK.passages.find(p=>p.label===s.classLevel); }
function showToast(msg,color="#2c3e6b") {
  const t=document.getElementById("toast");
  if(!t)return;
  t.textContent=msg; t.style.background=color; t.style.display="block";
  setTimeout(()=>t.style.display="none",2800);
}
