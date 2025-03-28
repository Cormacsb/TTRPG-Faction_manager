import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import uuid
from datetime import datetime


class NewspaperPanel(ttk.Frame):
    """Panel for creating and editing newspapers."""
    
    def __init__(self, parent, db_manager, district_repository, faction_repository, rumor_repository):
        """Initialize the newspaper panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            rumor_repository: Repository for rumor operations.
        """
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.rumor_repository = rumor_repository
        
        # Initialize state variables
        self.current_issue_id = None
        self.current_section = None
        self.current_article_id = None
        self.sections = ["Front Page", "Local News", "World News", "Rumors", "Advertisements"]
        
        self._create_widgets()
        self._load_issues()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Create main layout frames
        self.control_frame = ttk.Frame(self, padding="10 10 10 10", width=250)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.control_frame.pack_propagate(False)  # Fixed width
        
        self.editor_frame = ttk.Frame(self)
        self.editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Add controls to control frame
        ttk.Label(self.control_frame, text="Newspaper Editor", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Separator(self.control_frame).pack(fill=tk.X, pady=5)
        
        # Issue controls
        ttk.Label(self.control_frame, text="Issues:").pack(anchor=tk.W, pady=(10, 5))
        
        self.issues_frame = ttk.Frame(self.control_frame)
        self.issues_frame.pack(fill=tk.X, pady=5)
        
        self.issue_combobox = ttk.Combobox(self.issues_frame, state="readonly")
        self.issue_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.issue_combobox.bind("<<ComboboxSelected>>", self._on_issue_selected)
        
        ttk.Button(self.issues_frame, text="New", command=self._create_new_issue).pack(side=tk.LEFT, padx=5)
        
        # Issue properties
        self.issue_properties_frame = ttk.LabelFrame(self.control_frame, text="Issue Properties", padding="5 5 5 5")
        self.issue_properties_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.issue_properties_frame, text="Title:").grid(row=0, column=0, sticky=tk.W)
        self.title_entry = ttk.Entry(self.issue_properties_frame)
        self.title_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(self.issue_properties_frame, text="Issue Number:").grid(row=1, column=0, sticky=tk.W)
        self.issue_number_entry = ttk.Entry(self.issue_properties_frame)
        self.issue_number_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(self.issue_properties_frame, text="Publication Date:").grid(row=2, column=0, sticky=tk.W)
        self.date_entry = ttk.Entry(self.issue_properties_frame)
        self.date_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Button(self.issue_properties_frame, text="Save Changes", 
                  command=self._save_issue_properties).grid(row=3, column=0, columnspan=2, pady=5)
        
        self.issue_properties_frame.grid_columnconfigure(1, weight=1)
        
        # Section controls
        ttk.Label(self.control_frame, text="Sections:").pack(anchor=tk.W, pady=(10, 5))
        
        self.section_listbox = tk.Listbox(self.control_frame, height=5)
        self.section_listbox.pack(fill=tk.X)
        self.section_listbox.bind("<<ListboxSelect>>", self._on_section_selected)
        
        section_buttons_frame = ttk.Frame(self.control_frame)
        section_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(section_buttons_frame, text="Add", command=self._add_section).pack(side=tk.LEFT)
        ttk.Button(section_buttons_frame, text="Remove", command=self._remove_section).pack(side=tk.LEFT, padx=5)
        
        # Article controls
        ttk.Label(self.control_frame, text="Articles:").pack(anchor=tk.W, pady=(10, 5))
        
        self.article_listbox = tk.Listbox(self.control_frame, height=8)
        self.article_listbox.pack(fill=tk.X)
        self.article_listbox.bind("<<ListboxSelect>>", self._on_article_selected)
        
        article_buttons_frame = ttk.Frame(self.control_frame)
        article_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(article_buttons_frame, text="New", command=self._create_new_article).pack(side=tk.LEFT)
        ttk.Button(article_buttons_frame, text="Delete", command=self._delete_article).pack(side=tk.LEFT, padx=5)
        
        # Generate controls
        ttk.Separator(self.control_frame).pack(fill=tk.X, pady=5)
        
        ttk.Button(self.control_frame, text="Auto-Generate Articles", 
                  command=self._auto_generate_articles).pack(anchor=tk.W, pady=5)
        
        ttk.Button(self.control_frame, text="Publish Newspaper", 
                  command=self._publish_newspaper).pack(anchor=tk.W, pady=5)
        
        # Editor frame
        self.editor_frame_label = ttk.Label(self.editor_frame, text="Article Editor", font=("Arial", 12, "bold"))
        self.editor_frame_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Article properties
        self.article_properties_frame = ttk.LabelFrame(self.editor_frame, text="Article Properties", padding="5 5 5 5")
        self.article_properties_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.article_properties_frame, text="Headline:").grid(row=0, column=0, sticky=tk.W)
        self.headline_entry = ttk.Entry(self.article_properties_frame)
        self.headline_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(self.article_properties_frame, text="Author:").grid(row=1, column=0, sticky=tk.W)
        self.author_entry = ttk.Entry(self.article_properties_frame)
        self.author_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.article_properties_frame.grid_columnconfigure(1, weight=1)
        
        # Text editor
        self.editor_textarea_frame = ttk.Frame(self.editor_frame, padding="5 5 5 5")
        self.editor_textarea_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(self.editor_textarea_frame, text="Content:").pack(anchor=tk.W)
        
        # Text editor with scrollbar
        self.text_frame = ttk.Frame(self.editor_textarea_frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(self.text_frame, wrap=tk.WORD, undo=True, height=20)
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.text_scrollbar = ttk.Scrollbar(self.text_frame, command=self.content_text.yview)
        self.text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.content_text.config(yscrollcommand=self.text_scrollbar.set)
        
        # Editor buttons
        self.editor_buttons_frame = ttk.Frame(self.editor_frame, padding="5 5 5 5")
        self.editor_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(self.editor_buttons_frame, text="Save Article", 
                  command=self._save_article).pack(side=tk.LEFT)
        
        ttk.Button(self.editor_buttons_frame, text="Preview", 
                  command=self._preview_article).pack(side=tk.LEFT, padx=5)
        
        # Initially disable editor
        self._set_editor_enabled(False)
    
    def _load_issues(self):
        """Load newspaper issues from database."""
        try:
            query = """
                SELECT id, title, issue_number, publication_date
                FROM newspaper_issues
                ORDER BY issue_number DESC
            """
            
            issues = self.db_manager.execute_query(query)
            
            # Populate issues combobox
            self.issue_combobox['values'] = [f"Issue #{row['issue_number']}: {row['title']}" for row in issues]
            
            # Store issue IDs for reference
            self.issue_ids = [row['id'] for row in issues]
            
            # Select latest issue if any
            if issues:
                self.issue_combobox.current(0)
                self._on_issue_selected(None)
        except Exception as e:
            print(f"Error loading issues: {str(e)}")
    
    def _on_issue_selected(self, event):
        """Handle issue selection from combobox.
        
        Args:
            event: Selection event.
        """
        selection = self.issue_combobox.current()
        if selection >= 0 and selection < len(self.issue_ids):
            self.current_issue_id = self.issue_ids[selection]
            self._load_issue_data()
    
    def _load_issue_data(self):
        """Load data for the current issue."""
        if not self.current_issue_id:
            return
        
        try:
            # Get issue details
            query = """
                SELECT title, issue_number, publication_date
                FROM newspaper_issues
                WHERE id = :issue_id
            """
            
            issue = self.db_manager.execute_query(query, {"issue_id": self.current_issue_id})
            
            if not issue:
                return
            
            # Populate issue properties
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, issue[0]['title'])
            
            self.issue_number_entry.delete(0, tk.END)
            self.issue_number_entry.insert(0, str(issue[0]['issue_number']))
            
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, issue[0]['publication_date'])
            
            # Load sections for this issue
            self._load_sections()
        except Exception as e:
            print(f"Error loading issue data: {str(e)}")
    
    def _load_sections(self):
        """Load sections for the current issue."""
        if not self.current_issue_id:
            return
        
        try:
            # Get unique sections from articles
            query = """
                SELECT DISTINCT section
                FROM newspaper_articles
                WHERE issue_id = :issue_id
                ORDER BY section
            """
            
            sections = self.db_manager.execute_query(query, {"issue_id": self.current_issue_id})
            
            # Populate section listbox
            self.section_listbox.delete(0, tk.END)
            
            # Add default sections if none exist
            if not sections:
                for section in self.sections:
                    self.section_listbox.insert(tk.END, section)
            else:
                # Add existing sections
                for row in sections:
                    self.section_listbox.insert(tk.END, row['section'])
            
            # Clear selected section
            self.current_section = None
            
            # Clear articles
            self.article_listbox.delete(0, tk.END)
            
            # Clear editor
            self._clear_editor()
        except Exception as e:
            print(f"Error loading sections: {str(e)}")
    
    def _on_section_selected(self, event):
        """Handle section selection from listbox.
        
        Args:
            event: Selection event.
        """
        selection = self.section_listbox.curselection()
        if selection:
            self.current_section = self.section_listbox.get(selection[0])
            self._load_articles()
    
    def _load_articles(self):
        """Load articles for the current section."""
        if not self.current_issue_id or not self.current_section:
            return
        
        try:
            # Get articles for this section
            query = """
                SELECT id, headline, author
                FROM newspaper_articles
                WHERE issue_id = :issue_id AND section = :section
                ORDER BY headline
            """
            
            articles = self.db_manager.execute_query(query, {
                "issue_id": self.current_issue_id,
                "section": self.current_section
            })
            
            # Populate article listbox
            self.article_listbox.delete(0, tk.END)
            
            for row in articles:
                self.article_listbox.insert(tk.END, row['headline'])
                # Store article ID for reference
                self.article_listbox.itemconfig(tk.END, {"article_id": row['id']})
            
            # Clear selected article
            self.current_article_id = None
            
            # Clear editor
            self._clear_editor()
        except Exception as e:
            print(f"Error loading articles: {str(e)}")
    
    def _on_article_selected(self, event):
        """Handle article selection from listbox.
        
        Args:
            event: Selection event.
        """
        selection = self.article_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_article_id = self.article_listbox.itemcget(index, "article_id")
            self._load_article_data()
    
    def _load_article_data(self):
        """Load data for the current article."""
        if not self.current_article_id:
            return
        
        try:
            # Get article details
            query = """
                SELECT headline, author, content
                FROM newspaper_articles
                WHERE id = :article_id
            """
            
            article = self.db_manager.execute_query(query, {"article_id": self.current_article_id})
            
            if not article:
                return
            
            # Populate editor
            self.headline_entry.delete(0, tk.END)
            self.headline_entry.insert(0, article[0]['headline'])
            
            self.author_entry.delete(0, tk.END)
            self.author_entry.insert(0, article[0]['author'] or "")
            
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, article[0]['content'] or "")
            
            # Enable editor
            self._set_editor_enabled(True)
        except Exception as e:
            print(f"Error loading article data: {str(e)}")
    
    def _create_new_issue(self):
        """Create a new newspaper issue."""
        try:
            # Get latest issue number
            query = """
                SELECT MAX(issue_number) as last_issue
                FROM newspaper_issues
            """
            
            result = self.db_manager.execute_query(query)
            
            next_issue = 1
            if result and result[0]['last_issue'] is not None:
                next_issue = result[0]['last_issue'] + 1
            
            # Get current turn number
            query = """
                SELECT current_turn
                FROM game_state
                WHERE id = 'current'
            """
            
            result = self.db_manager.execute_query(query)
            
            turn_number = 1
            if result:
                turn_number = result[0]['current_turn']
            
            # Create new issue
            issue_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            query = """
                INSERT INTO newspaper_issues (
                    id, issue_number, publication_date, title, created_at, updated_at
                )
                VALUES (
                    :id, :issue_number, :publication_date, :title, :created_at, :updated_at
                )
            """
            
            title = f"The Game Chronicle - Turn {turn_number}"
            
            with self.db_manager.connection:
                self.db_manager.execute_update(query, {
                    "id": issue_id,
                    "issue_number": next_issue,
                    "publication_date": now,
                    "title": title,
                    "created_at": now,
                    "updated_at": now
                })
            
            # Refresh issues list
            self._load_issues()
            
            # Select the new issue
            if self.issue_ids:
                self.issue_combobox.current(0)
                self._on_issue_selected(None)
            
            messagebox.showinfo("Success", "New issue created successfully.")
        except Exception as e:
            print(f"Error creating new issue: {str(e)}")
            messagebox.showerror("Error", f"Failed to create new issue: {str(e)}")
    
    def _save_issue_properties(self):
        """Save properties for the current issue."""
        if not self.current_issue_id:
            messagebox.showinfo("No Issue", "Please select or create an issue first.")
            return
        
        try:
            # Get values from fields
            title = self.title_entry.get()
            issue_number = self.issue_number_entry.get()
            publication_date = self.date_entry.get()
            
            # Validate input
            if not title:
                messagebox.showerror("Error", "Title is required.")
                return
                
            try:
                issue_number = int(issue_number)
            except ValueError:
                messagebox.showerror("Error", "Issue number must be a valid integer.")
                return
            
            # Update issue
            query = """
                UPDATE newspaper_issues SET
                    title = :title,
                    issue_number = :issue_number,
                    publication_date = :publication_date,
                    updated_at = :updated_at
                WHERE id = :issue_id
            """
            
            with self.db_manager.connection:
                self.db_manager.execute_update(query, {
                    "issue_id": self.current_issue_id,
                    "title": title,
                    "issue_number": issue_number,
                    "publication_date": publication_date,
                    "updated_at": datetime.now().isoformat()
                })
            
            # Refresh issues list
            self._load_issues()
            
            messagebox.showinfo("Success", "Issue properties saved successfully.")
        except Exception as e:
            print(f"Error saving issue properties: {str(e)}")
            messagebox.showerror("Error", f"Failed to save issue properties: {str(e)}")
    
    def _add_section(self):
        """Add a new section to the current issue."""
        if not self.current_issue_id:
            messagebox.showinfo("No Issue", "Please select or create an issue first.")
            return
        
        section_name = simpledialog.askstring("New Section", "Enter section name:")
        if not section_name:
            return
        
        # Check if section already exists
        for i in range(self.section_listbox.size()):
            if self.section_listbox.get(i) == section_name:
                messagebox.showinfo("Duplicate", "Section already exists.")
                return
        
        # Add to listbox
        self.section_listbox.insert(tk.END, section_name)
        
        # Select the new section
        self.section_listbox.selection_clear(0, tk.END)
        self.section_listbox.selection_set(tk.END)
        self.section_listbox.see(tk.END)
        
        # Update current section
        self.current_section = section_name
        
        # Clear articles
        self.article_listbox.delete(0, tk.END)
    
    def _remove_section(self):
        """Remove the selected section."""
        selection = self.section_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a section to remove.")
            return
        
        section_name = self.section_listbox.get(selection[0])
        
        # Check if section has articles
        if not self.current_issue_id:
            self.section_listbox.delete(selection[0])
            return
        
        try:
            query = """
                SELECT COUNT(*) as article_count
                FROM newspaper_articles
                WHERE issue_id = :issue_id AND section = :section
            """
            
            result = self.db_manager.execute_query(query, {
                "issue_id": self.current_issue_id,
                "section": section_name
            })
            
            article_count = result[0]['article_count'] if result else 0
            
            if article_count > 0:
                confirm = messagebox.askyesno("Confirm Delete", 
                                            f"Section '{section_name}' contains {article_count} articles. Delete anyway?")
                if not confirm:
                    return
                
                # Delete articles in section
                query = """
                    DELETE FROM newspaper_articles
                    WHERE issue_id = :issue_id AND section = :section
                """
                
                with self.db_manager.connection:
                    self.db_manager.execute_update(query, {
                        "issue_id": self.current_issue_id,
                        "section": section_name
                    })
            
            # Remove from listbox
            self.section_listbox.delete(selection[0])
            
            # Clear current section
            self.current_section = None
            
            # Clear articles
            self.article_listbox.delete(0, tk.END)
            
            # Clear editor
            self._clear_editor()
            
        except Exception as e:
            print(f"Error removing section: {str(e)}")
            messagebox.showerror("Error", f"Failed to remove section: {str(e)}")
    
    def _create_new_article(self):
        """Create a new article in the current section."""
        if not self.current_issue_id:
            messagebox.showinfo("No Issue", "Please select or create an issue first.")
            return
            
        if not self.current_section:
            messagebox.showinfo("No Section", "Please select a section first.")
            return
        
        try:
            # Create new article
            article_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            query = """
                INSERT INTO newspaper_articles (
                    id, issue_id, section, headline, content, created_at, updated_at
                )
                VALUES (
                    :id, :issue_id, :section, :headline, :content, :created_at, :updated_at
                )
            """
            
            with self.db_manager.connection:
                self.db_manager.execute_update(query, {
                    "id": article_id,
                    "issue_id": self.current_issue_id,
                    "section": self.current_section,
                    "headline": "New Article",
                    "content": "",
                    "created_at": now,
                    "updated_at": now
                })
            
            # Refresh articles list
            self._load_articles()
            
            # Select the new article
            for i in range(self.article_listbox.size()):
                if self.article_listbox.itemcget(i, "article_id") == article_id:
                    self.article_listbox.selection_clear(0, tk.END)
                    self.article_listbox.selection_set(i)
                    self.article_listbox.see(i)
                    self.current_article_id = article_id
                    self._load_article_data()
                    break
        except Exception as e:
            print(f"Error creating new article: {str(e)}")
            messagebox.showerror("Error", f"Failed to create new article: {str(e)}")
    
    def _delete_article(self):
        """Delete the selected article."""
        if not self.current_article_id:
            messagebox.showinfo("No Selection", "Please select an article to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this article?")
        if not confirm:
            return
        
        try:
            query = """
                DELETE FROM newspaper_articles
                WHERE id = :article_id
            """
            
            with self.db_manager.connection:
                self.db_manager.execute_update(query, {"article_id": self.current_article_id})
            
            # Refresh articles list
            self._load_articles()
            
            # Clear editor
            self._clear_editor()
            
            messagebox.showinfo("Success", "Article deleted successfully.")
        except Exception as e:
            print(f"Error deleting article: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete article: {str(e)}")
    
    def _save_article(self):
        """Save the current article."""
        if not self.current_article_id:
            messagebox.showinfo("No Article", "Please select or create an article first.")
            return
        
        try:
            # Get values from fields
            headline = self.headline_entry.get()
            author = self.author_entry.get()
            content = self.content_text.get(1.0, tk.END).strip()
            
            # Validate input
            if not headline:
                messagebox.showerror("Error", "Headline is required.")
                return
            
            # Update article
            query = """
                UPDATE newspaper_articles SET
                    headline = :headline,
                    author = :author,
                    content = :content,
                    updated_at = :updated_at
                WHERE id = :article_id
            """
            
            with self.db_manager.connection:
                self.db_manager.execute_update(query, {
                    "article_id": self.current_article_id,
                    "headline": headline,
                    "author": author,
                    "content": content,
                    "updated_at": datetime.now().isoformat()
                })
            
            # Refresh articles list
            selection = self.article_listbox.curselection()
            if selection:
                index = selection[0]
                self.article_listbox.delete(index)
                self.article_listbox.insert(index, headline)
                self.article_listbox.itemconfig(index, {"article_id": self.current_article_id})
                self.article_listbox.selection_set(index)
            
            messagebox.showinfo("Success", "Article saved successfully.")
        except Exception as e:
            print(f"Error saving article: {str(e)}")
            messagebox.showerror("Error", f"Failed to save article: {str(e)}")
    
    def _auto_generate_articles(self):
        """Auto-generate articles based on game state."""
        if not self.current_issue_id:
            messagebox.showinfo("No Issue", "Please select or create an issue first.")
            return
        
        # Get game state
        try:
            # Get current turn
            query = """
                SELECT current_turn
                FROM game_state
                WHERE id = 'current'
            """
            
            result = self.db_manager.execute_query(query)
            
            turn_number = result[0]['current_turn'] if result else 1
            
            # Get rumors
            rumors = []
            for rumor in self.rumor_repository.find_all():
                # Get district
                district = self.district_repository.find_by_id(rumor.district_id)
                if district:
                    rumors.append({
                        "id": rumor.id,
                        "text": rumor.rumor_text,
                        "district_name": district.name
                    })
            
            # Get factions
            factions = {faction.id: faction.name for faction in self.faction_repository.find_all()}
            
            # Get districts
            districts = {district.id: district.name for district in self.district_repository.find_all()}
            
            # Generate articles
            articles = []
            
            # Front page main story
            articles.append({
                "section": "Front Page",
                "headline": f"Turn {turn_number}: The Week in Review",
                "author": "Editor in Chief",
                "content": (
                    f"Welcome to issue #{self.issue_number_entry.get()} of The Game Chronicle, "
                    f"your trusted source for all the news across the realm.\n\n"
                    f"This week has seen significant developments across the territories, "
                    f"with several factions jockeying for position and influence. "
                    f"Read on for our detailed coverage of all the important events."
                )
            })
            
            # Generate some fiction articles
            district_news = []
            for district_id, district_name in districts.items():
                district_news.append({
                    "section": "Local News",
                    "headline": f"Happenings in {district_name}",
                    "author": "Local Correspondent",
                    "content": (
                        f"The streets of {district_name} have been bustling this week "
                        f"with unusual activity. Several factions have been seen operating "
                        f"in the area, though their exact intentions remain unknown.\n\n"
                        f"Local authorities report that the situation remains under control, "
                        f"but citizens are advised to stay vigilant and report any suspicious activity."
                    )
                })
            
            # Only use a random selection of district news
            import random
            random.shuffle(district_news)
            articles.extend(district_news[:min(3, len(district_news))])
            
            # Generate rumor articles
            for rumor in rumors[:min(5, len(rumors))]:
                articles.append({
                    "section": "Rumors",
                    "headline": f"Whispers from {rumor['district_name']}",
                    "author": "Anonymous Source",
                    "content": rumor["text"]
                })
            
            # Generate faction activity articles
            for faction_id, faction_name in factions.items():
                articles.append({
                    "section": "World News",
                    "headline": f"{faction_name} Makes Strategic Moves",
                    "author": "Political Correspondent",
                    "content": (
                        f"Sources close to {faction_name} report that the faction has been "
                        f"making strategic moves to expand their influence across several territories. "
                        f"While the exact nature of these operations remains classified, "
                        f"observers note a noticeable increase in their activity.\n\n"
                        f"Rival factions have responded with their own countermeasures, "
                        f"leading to a delicate balance of power in the affected regions."
                    )
                })
            
            # Only use a random selection of faction news
            random.shuffle(articles)
            
            # Insert articles into database
            count = 0
            now = datetime.now().isoformat()
            
            query = """
                INSERT INTO newspaper_articles (
                    id, issue_id, section, headline, author, content, created_at, updated_at
                )
                VALUES (
                    :id, :issue_id, :section, :headline, :author, :content, :created_at, :updated_at
                )
            """
            
            with self.db_manager.connection:
                for article in articles:
                    # Check if an article with this headline already exists
                    check_query = """
                        SELECT 1
                        FROM newspaper_articles
                        WHERE issue_id = :issue_id AND headline = :headline
                    """
                    
                    exists = self.db_manager.execute_query(check_query, {
                        "issue_id": self.current_issue_id,
                        "headline": article["headline"]
                    })
                    
                    if exists:
                        continue
                    
                    self.db_manager.execute_update(query, {
                        "id": str(uuid.uuid4()),
                        "issue_id": self.current_issue_id,
                        "section": article["section"],
                        "headline": article["headline"],
                        "author": article.get("author", ""),
                        "content": article["content"],
                        "created_at": now,
                        "updated_at": now
                    })
                    
                    count += 1
            
            # Refresh sections and articles
            self._load_sections()
            
            messagebox.showinfo("Success", f"Generated {count} articles successfully.")
        except Exception as e:
            print(f"Error auto-generating articles: {str(e)}")
            messagebox.showerror("Error", f"Failed to auto-generate articles: {str(e)}")
    
    def _preview_article(self):
        """Preview the current article."""
        if not self.current_article_id:
            messagebox.showinfo("No Article", "Please select or create an article first.")
            return
        
        headline = self.headline_entry.get()
        author = self.author_entry.get()
        content = self.content_text.get(1.0, tk.END).strip()
        
        # Create preview window
        preview_window = tk.Toplevel(self)
        preview_window.title("Article Preview")
        preview_window.geometry("600x600")
        
        # Create preview content
        frame = ttk.Frame(preview_window, padding="20 20 20 20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=headline, font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        if author:
            ttk.Label(frame, text=f"By {author}", font=("Arial", 10, "italic")).pack(anchor=tk.W, pady=(0, 20))
        
        text = tk.Text(frame, wrap=tk.WORD, height=20, width=80)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
        
        ttk.Button(frame, text="Close", command=preview_window.destroy).pack(pady=20)
    
    def _publish_newspaper(self):
        """Publish the current newspaper issue."""
        if not self.current_issue_id:
            messagebox.showinfo("No Issue", "Please select or create an issue first.")
            return
        
        # Check if issue has content
        try:
            query = """
                SELECT COUNT(*) as article_count
                FROM newspaper_articles
                WHERE issue_id = :issue_id
            """
            
            result = self.db_manager.execute_query(query, {"issue_id": self.current_issue_id})
            
            article_count = result[0]['article_count'] if result else 0
            
            if article_count == 0:
                messagebox.showinfo("Empty Issue", "Cannot publish an empty issue. Please add some articles first.")
                return
            
            # TODO: Implement actual publishing logic
            # This could involve generating PDFs, distributing to factions, etc.
            
            messagebox.showinfo("Success", "Newspaper published successfully.")
        except Exception as e:
            print(f"Error publishing newspaper: {str(e)}")
            messagebox.showerror("Error", f"Failed to publish newspaper: {str(e)}")
    
    def _clear_editor(self):
        """Clear the article editor."""
        self.headline_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.content_text.delete(1.0, tk.END)
        self._set_editor_enabled(False)
    
    def _set_editor_enabled(self, enabled):
        """Enable or disable the article editor.
        
        Args:
            enabled (bool): Whether to enable the editor.
        """
        state = "normal" if enabled else "disabled"
        self.headline_entry.config(state=state)
        self.author_entry.config(state=state)
        self.content_text.config(state=state)
    
    def refresh(self):
        """Refresh the newspaper panel data."""
        self._load_issues()