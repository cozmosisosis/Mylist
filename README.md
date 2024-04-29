<h1>MyList</h1>

<h5>You can save time and avoid forgeting <b><i>ANYTHING</i></b> when you use MyList</h5>

<br>
<br>


<h3>What Can It Be Used For?</h3>
<hr>
<h5><p>Any type of list ( primarily ones that you have or will repeat ) :</p></h5>

<ul><h6>
	<li>Grocery lists</li>
	<li>List of Chores</li>
	<li>Ingredients for a recepie</li>
</h6></ul>

<br>
<br>

<h3>Primary Functions</h3>
<hr>


<h5><p>
	Quickly create a list of items with custom names and quantities
</p></h5>
	<ul><h6>
	<li>
		Enter the name and quantity of the item you want on the list. It is that easy.
	</li>
	</h6></ul>	


<h5><p>
	Quick add custom made recipes
</p></h5>
	<ul><h6>
	<li>
		If you make pizza often you can make a pizza group. Add all the ingredients you need to make pizza to the group and it is ready for use. Next time you plan to go
		grocery shopping and you decide you want pizza, all you need to do is select the pizza group to add to list and then verify all items on the list before adding. 
		This allows you to avoid adding ingredients that you may already have enough of.
	</li>
	</h6></ul>


<h5><p>
	All previously added items are saved in the db ( unless you want to delete them )
</p></h5>
	<ul><h6>
	<li>
		With all previous items saved you can look back through all items you have added to check if there is anything you 
		may have forgoten to add.
	</li>
	</h6></ul>


<br>
<br>
<br>


<h3>Is This App For You?</h3>
<hr>

<ul><h6>
  <li>Have you ever forgotten to write something on a grocery list that you new you needed but just didn't remember when you made the list?</li>
  <li>Do you look up the ingredients for the same recepy over and over?</li>
  <li>Have you remade the same packing list every time you travel?</li>
  <li>Or make the same todo lists every year for spring cleaning?</li>
</h6></ul>

<p>If so, the tools this app offers allow all these issues to be avoided.</p>
<br>



<br>
<br>
<br>
<br>

<h3>How To Install And Run Locally</h3>
<hr>

<h5><p>
	Ensure you have python3 installed
</p></h5>
<br>

<h5><p>
	Clone The Repository
</p></h5>

```git
	git clone https://github.com/cozmosisosis/Mylist.git
```
<br>

<h5><p>
	Create a python venv
	<br>
	<br>
	If linux/mac:
</p></h5>

```python
	py -3 -m venv .venv
```
<br>
<h5><p>
	If windows:
</p></h5>

```python
	python3 -m venv .venv
```
<br>

<h5><p>
	Activate venv:
	<br>
	<br>
	If linux/mac:
</p></h5>

```python
	. .venv/bin/activate
```
<br>
<h5><p>
	If windows:
</p></h5>

```python
	. .venv/scripts/activate
```

<br>
<h5><p>
	Once venv is activated run:
</p></h5>

```python
	pip install -r requirements.txt
```

<br>
<h5><p>
	Finnaly you can run the application locally:
</p></h5>

```python
	flask run
```
