import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
  model="gpt-4-0613",
  messages=[
    {
      "role": "system",
      "content": "You are a world-class translator of ancient books. Here are translations of some of the special terms:\n\n- Holy Eucharist = Святая Евхаристия\n- Eucharist Service = Служба Евхаристии\n- Service = Служба\n- Collect = Сбор\n- Sacrament = Священнодействие\n- Low Celebration = Малое Празднование\n- High Celebration = Великое Празднование\n- Liberal Catholic Church = Либеральная Католическая Церковь\n- Buddhic = будхический\n- mental matter = ментальная материя\n\nNow translate every paragraph below to Russian. Carefully translate all paragraphs. Keep in mind that this text is about Catholic Church, and thus you must use appropriate style and terminology. Don't ever switch back to writing English: you must always translate to Russian. Don't generate markdown. Your output must read like a good book."
    },
    {
      "role": "user",
      "content": "THE idea that clairvoyant observation is possible is no longer regarded as entirely insane. It is not generally accepted, nor indeed is it accepted to any large extent. A constantly growing minority, however, of fairly intelligent people believe clairvoyance to be a fact, and regard it as a perfectly natural power, which will become universal in the course of evolution. They do not regard it as a miraculous gift, nor as an outgrowth from high spirituality, lofty intelligence, or purity of character; any or all of these may be manifested in a person who is not in the least clairvoyant. They know that it is a power latent in all men, and that it can be developed by any one who is able and willing to pay the price demanded for its forcing, ahead of the general evolution."
    }
  ],
  temperature=1.00,
  max_tokens=1024,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)

print(response.choices[0].message.content)
