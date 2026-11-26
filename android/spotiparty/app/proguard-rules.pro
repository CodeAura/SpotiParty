# Keep class and method names: readable stack traces matter more than the last few KB in a sideloaded app.
-dontobfuscate
# window.SpotiPartyTV: only the web page calls these, so R8 would think they are unused.
-keepclassmembers class io.github.cleanyourtv.partymode.TvBridge {
    @android.webkit.JavascriptInterface <methods>;
}
