document.addEventListener("click",function(e){
var b=e.target.closest("[data-copy]");if(!b)return;
var u=b.getAttribute("data-copy");
function done(){var s=b.querySelector("span");var o=s.textContent;s.textContent="✓";setTimeout(function(){s.textContent=o},1400)}
if(navigator.clipboard){navigator.clipboard.writeText(u).then(done,function(){prompt("Copy:",u)})}else{prompt("Copy:",u)}
});