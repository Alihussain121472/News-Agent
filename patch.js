  async function generateVisual(prompt, apiKey, model = 'gpt-image-2') {
    if (!apiKey || !String(prompt || '').trim()) return null;
    const realModel = model === 'gpt-image-2' ? 'dall-e-3' : model;
    const response = await fetch('https://api.openai.com/v1/images/generations', {
      method: 'POST', headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: realModel, prompt: String(prompt).slice(0, 4000), size: '1024x1024', quality: 'standard', n: 1 }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || 'Image generation failed.');
    const url = result.data?.[0]?.url;
    if (!url) throw new Error('The image service returned no image.');
    const imgResponse = await fetch(url);
    const buffer = await imgResponse.arrayBuffer();
    const fileName = `${crypto.randomUUID()}.png`;
    fs.writeFileSync(path.join(mediaDir, fileName), Buffer.from(buffer));
    return `/media/${fileName}`;
  }

  async function generate(topic, objective, sourceText = '') {
    const saved = settings();
    const platforms = normalizePlatforms(saved.config);
    const apiKey = saved.secrets?.openaiApiKey || process.env.OPENAI_API_KEY;
    if (!apiKey) return demoGeneration(topic, objective, platforms, saved.config?.brand || {});
    const prompt = `${masterPrompt}\n\nBRAND CONFIG:\n${JSON.stringify(saved.config)}\n\nENABLED PLATFORMS:\n${JSON.stringify(platforms)}\n\nWEBSITE SOURCE TEXT:\n${sourceText || 'No website source was supplied. Do not invent website claims.'}\n\nCURRENT REQUEST:\nTopic: ${topic}\nObjective: ${objective || 'Educate and engage'}\nCreate a truthful conversion path to the configured website or registration page. Return exactly one item in the drafts array for every enabled platform. Rotate formats across image posts, stories, and reel scripts. Return only the JSON object specified in the output format.`;
    
    let realModel = saved.secrets?.openaiModel || 'gpt-4o-mini';
    if (realModel === 'gpt-5-mini') realModel = 'gpt-4o-mini';

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: realModel, messages: [{role: 'user', content: prompt}] }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || 'AI generation failed.');
    
    const textContent = result.choices?.[0]?.message?.content || '';
    const generated = parseGeneratedJson(textContent);
    if (!generated || !Array.isArray(generated.drafts)) throw new Error('The writing service returned an incomplete draft. Please generate again.');
    return generated;
  }
