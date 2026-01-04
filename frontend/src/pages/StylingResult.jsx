export default function StylingResults({ data }) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <h1 className="text-3xl font-bold mb-6">AI Styling Suggestions</h1>
  
        <div className="bg-white shadow-lg rounded-2xl p-6 space-y-6">
  
          {/* Hairstyle */}
          <section>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              ✂️ Hairstyle
            </h2>
            <p className="font-medium mt-1">{data.hairstyle}</p>
            <p className="text-gray-600 mt-1">{data.hairstyle_description}</p>
          </section>
  
          {/* Beard */}
          <section>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              🧔 Beard Style
            </h2>
            <p className="font-medium mt-1">{data.beard}</p>
            <p className="text-gray-600 mt-1">{data.beard_description}</p>
          </section>
  
          {/* Outfit */}
          <section>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              👔 Outfit
            </h2>
            <p className="text-gray-700 whitespace-pre-line">{data.outfit}</p>
          </section>
  
          {/* Gender + Skin Tone */}
          <div className="flex justify-between text-gray-700">
            <p>⚧ Gender: <span className="font-medium">{data.gender}</span></p>
            <p>🎨 Skin Tone: <span className="font-medium">{data.skin_tone}</span></p>
          </div>
        </div>
  
        <div className="flex justify-between mt-8">
          <button className="px-4 py-2 bg-gray-300 rounded-xl">⬅ Back</button>
          <button className="px-5 py-2 bg-blue-600 text-white rounded-xl shadow">
            ⭐ Save Look
          </button>
        </div>
      </div>
    );
  }
  