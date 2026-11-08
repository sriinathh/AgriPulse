import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sprout, Search, Globe2, ArrowRight, Droplets, Activity, Leaf, BarChart3, Menu, X } from 'lucide-react';

const languages = [
  'Afrikaans','Akan','Albanian','Amharic','Arabic','Armenian','Assamese','Azerbaijani','Basque','Belarusian','Bengali','Bosnian','Bulgarian','Burmese',
  'Catalan','Cebuano','Chinese (Simplified)','Chinese (Traditional)','Corsican','Croatian','Czech','Danish','Dhivehi','Dutch','English','Esperanto','Estonian',
  'Filipino','Finnish','French','Frisian','Galician','Georgian','German','Greek','Gujarati','Haitian Creole','Hausa','Hawaiian','Hebrew','Hindi','Hmong','Hungarian',
  'Icelandic','Igbo','Indonesian','Irish','Italian','Japanese','Javanese','Kannada','Kazakh','Khmer','Kinyarwanda','Korean','Kurdish','Kyrgyz','Lao','Latin','Latvian',
  'Lithuanian','Luxembourgish','Macedonian','Malagasy','Malay','Malayalam','Maltese','Maori','Marathi','Mongolian','Nepali','Norwegian','Odia','Pashto','Persian','Polish',
  'Portuguese','Punjabi','Romanian','Russian','Samoan','Scots Gaelic','Serbian','Sesotho','Shona','Sindhi','Sinhala','Slovak','Slovenian','Somali','Spanish','Sundanese',
  'Swahili','Swedish','Tajik','Tamil','Tatar','Telugu','Thai','Turkish','Turkmen','Ukrainian','Urdu','Uyghur','Uzbek','Vietnamese','Welsh','Xhosa','Yiddish','Yoruba','Zulu'
];
const links = [{label:'Home',id:'home'},{label:'About',id:'how-it-works'},{label:'Features',id:'features'},{label:'Impact',id:'impact'},{label:'Blog',id:'blog'},{label:'Contact',id:'contact'}];

export const LandingPage: React.FC = () => {
  const [language,setLanguage] = useState(localStorage.getItem('agripulse-language') || 'English');
  const [query,setQuery] = useState('');
  const [menuOpen,setMenuOpen] = useState(false);
  const [languageOpen,setLanguageOpen] = useState(false);
  const [languageSearch,setLanguageSearch] = useState('');
  const features = [
    {icon:Droplets,title:'Smart Irrigation',desc:'Use water where and when crops need it.'},
    {icon:BarChart3,title:'Data Driven',desc:'Turn field readings into clearer decisions.'},
    {icon:Leaf,title:'Sustainable Farming',desc:'Support healthier soil and a greener future.'},
    {icon:Activity,title:'Live Monitoring',desc:'Keep track of sensors, weather and field health.'}
  ];
  const filtered = useMemo(()=>features.filter(f=>(f.title+' '+f.desc).toLowerCase().includes(query.toLowerCase())),[query]);
  return <main className="agri-site">
    <header className="agri-header">
      <Link to="/" className="agri-brand"><span className="brand-mark"><Sprout size={27}/></span><span><b>AgriPulse</b><small>Smart Farming · Sustainable Future</small></span></Link>
      <nav className={menuOpen?'agri-nav open':'agri-nav'}>{links.map(l=><a key={l.id} href={'#'+l.id}>{l.label}</a>)}</nav>
      <div className="agri-header-actions">
        <div className="language-picker">
          <button className="language-select" type="button" aria-label="Choose language" aria-expanded={languageOpen} onClick={()=>setLanguageOpen(!languageOpen)}><Globe2 size={16}/><span>{language}</span><span className="language-chevron">⌄</span></button>
          {languageOpen && <div className="language-menu">
            <div className="language-search"><Search size={15}/><input autoFocus aria-label="Search languages" placeholder="Search languages…" value={languageSearch} onChange={e=>setLanguageSearch(e.target.value)}/></div>
            <div className="language-options">{languages.filter(l=>l.toLowerCase().includes(languageSearch.toLowerCase())).map(l=><button type="button" key={l} className={language===l?'selected':''} onClick={()=>{setLanguage(l);localStorage.setItem('agripulse-language',l);setLanguageOpen(false);setLanguageSearch('')}}>{l}{language===l&&<span>✓</span>}</button>)}
            {languages.filter(l=>l.toLowerCase().includes(languageSearch.toLowerCase())).length===0&&<p className="language-empty">No languages found</p>}</div>
          </div>}
        </div>
        <Link to="/auth" className="agri-cta small">Sign in <ArrowRight size={16}/></Link>
        <button className="mobile-menu" onClick={()=>setMenuOpen(!menuOpen)} aria-label="Toggle menu">{menuOpen?<X/>:<Menu/>}</button>
      </div>
    </header>
    <section className="agri-hero" id="home">
      <div className="hero-shade"/>
      <div className="hero-copy">
        <span className="eyebrow"><span/> SMART IRRIGATION&nbsp; · &nbsp;AI POWERED&nbsp; · &nbsp;DATA DRIVEN</span>
        <h1><span>Better Crops</span><br/><em>Brighter Future</em></h1>
        <p>AgriPulse helps farmers make smarter decisions with real-time data, AI and sustainable farming practices for a healthier planet.</p>
        <div className="hero-search"><Search size={19}/><input aria-label="Search features" placeholder="Search smart farming features..." value={query} onChange={e=>setQuery(e.target.value)}/>{query&&<button onClick={()=>setQuery('')}>Clear</button>}</div>
        <div className="hero-actions"><Link to="/auth?mode=signup" className="agri-cta">Get Started <ArrowRight size={18}/></Link><a href="#how-it-works" className="learn-link"><span className="play">▶</span> Learn More</a></div>
        <div className="hero-proof"><span className="proof-icon"><Leaf size={19}/></span><span><b>Smarter farming starts here</b><small>Practical insights for a more sustainable tomorrow.</small></span></div>
      </div>
      <div className="hero-image-caption"><span className="live-dot"/> Precision agriculture, naturally.</div>
    </section>
    <section className="feature-section" id="features">
      <div className="section-heading"><span className="eyebrow dark">BUILT FOR EVERY FIELD</span><h2>Good decisions. <em>Healthier harvests.</em></h2><p>Everything you need to understand your farm and use resources wisely.</p></div>
      <div className="feature-grid">{filtered.map(f=><article className="feature-card" key={f.title}><div className="feature-icon"><f.icon size={23}/></div><h3>{f.title}</h3><p>{f.desc}</p></article>)}
      {filtered.length===0&&<p className="no-results">No matching features. Try “water”, “data” or “weather”.</p>}</div>
    </section>
    <section className="impact-strip" id="impact"><div><span className="eyebrow">GROW WITH PURPOSE</span><h2>Technology that works <em>with nature.</em></h2></div><p>From real-time soil readings to weather-aware irrigation recommendations, AgriPulse helps bring clarity to everyday farm decisions.</p></section>
    <section className="how-section" id="how-it-works"><div className="how-photo"/><div><span className="eyebrow dark">SIMPLE BY DESIGN</span><h2>Your farm, at a <em>glance.</em></h2><p>Connect your fields and sensors, review the latest readings, and explore recommendations from one easy-to-use dashboard.</p><Link to="/auth?mode=signup" className="agri-cta">Start your journey <ArrowRight size={18}/></Link></div></section>
    <footer className="agri-footer" id="contact"><Link to="/" className="agri-brand"><span className="brand-mark"><Sprout size={22}/></span><span><b>AgriPulse</b><small>Smart Farming · Sustainable Future</small></span></Link><span>Growing a smarter, greener future.</span><Link to="/auth">Sign in / Sign up</Link></footer>
  </main>;
};
